% waveform definition

cfgVHT = wlanVHTConfig;            % Create packet configuration
cfgVHT.ChannelBandwidth = 'CBW80'; % 80 MHz
cfgVHT.NumTransmitAntennas = 1;    % One transmit antenna
cfgVHT.NumSpaceTimeStreams = 1;    % One space-time stream
cfgVHT.STBC = false;               % No STBC so one spatial stream
cfgVHT.MCS = 8;                    % Modulation: 256 QAM
cfgVHT.APEPLength = 3000;          % A-MPDU length pre-EOF padding in bytes

% specify the number of packets and the time inbetween

numPackets = 20;  % Generate 20 packets
idleTime = 10e-6; % 10 microseconds idle time between packets

% Create random data; PSDULength is in bytes
savedState = rng(0); % Set random state
data = randi([0 1],cfgVHT.PSDULength*8*numPackets,1);

% Generate a multi-packet waveform
txWaveform = wlanWaveformGenerator(data,cfgVHT, ...
    'NumPackets',numPackets,'IdleTime',idleTime);

% Get the sampling rate of the waveform
fs = wlanSampleRate(cfgVHT);
disp(['Baseband sampling rate: ' num2str(fs/1e6) ' Msps']);

% Oversample the waveform
osf = 3;         % Oversampling factor
filterLen = 120; % Filter length
beta = 0.5;      % Design parameter for Kaiser window

% Generate filter coefficients
coeffs = osf.*firnyquist(filterLen,osf,kaiser(filterLen+1,beta));
coeffs = coeffs(1:end-1); % Remove trailing zero
interpolationFilter = dsp.FIRInterpolator(osf,'Numerator',coeffs);
txWaveform = interpolationFilter(txWaveform);

% Plot the magnitude and phase response of the filter applied after
% oversampling
h = fvtool(interpolationFilter);
h.Analysis = 'freq';           % Plot magnitude and phase responses
h.FS = osf*fs;                 % Set sampling rate
h.NormalizedFrequency = 'off'; % Plot responses against frequency

hpaBackoff = 8; % dB

% Create and configure a memoryless nonlinearity to model the amplifier
nonLinearity = comm.MemorylessNonlinearity;
nonLinearity.Method = 'Rapp model';
nonLinearity.Smoothness = 3; % p parameter
nonLinearity.LinearGain = -hpaBackoff;

% Apply the model to each transmit antenna
for i=1:cfgVHT.NumTransmitAntennas
    txWaveform(:,i) = nonLinearity(txWaveform(:,i));
end

% Thermal noise is added to the waveform with a 6dB noise
NF = 6;         % Noise figure (dB)
BW = fs*osf;    % Bandwidth (Hz)
k = 1.3806e-23; % Boltzman constant (J/K)
T = 290;        % Ambient temperature (K)
noisePower = 10*log10(k*T*BW)+NF;

awgnChannel = comm.AWGNChannel('NoiseMethod','Variance', ...
    'Variance',10^(noisePower/10));
txWaveform = awgnChannel(txWaveform);

% Resample to baseband
decimationFilter = dsp.FIRDecimator(osf,'Numerator',coeffs);
rxWaveform = decimationFilter(txWaveform);

% Configure VHT Data symbol recovery
cfgRec = wlanRecoveryConfig;
cfgRec.EqualizationMethod = 'ZF';    % Use zero forcing algorithm
cfgRec.PilotPhaseTracking = 'PreEQ'; % Use pilot phase tracking

EVMPerPkt = comm.EVM;
EVMPerPkt.AveragingDimensions = [1 2 3]; % Nst-by-Nsym-by-Nss
EVMPerPkt.Normalization = 'Average constellation power';
EVMPerPkt.ReferenceSignalSource  = 'Estimated from reference constellation';
EVMPerPkt.ReferenceConstellation = helperReferenceSymbols(cfgVHT);

% Measure average EVM over symbols
EVMPerSC = comm.EVM;
EVMPerSC.AveragingDimensions = 2; % Nst-by-Nsym-by-Nss
EVMPerSC.Normalization = 'Average constellation power';
EVMPerSC.ReferenceSignalSource  = 'Estimated from reference constellation';
EVMPerSC.ReferenceConstellation = helperReferenceSymbols(cfgVHT);

% Indices for accessing each field within the time-domain packet
ind = wlanFieldIndices(cfgVHT);

rxWaveformLength = size(rxWaveform,1);
pktLength = double(ind.VHTData(2));

% Minimum length of data we can detect; length of the L-STF in samples
minPktLen = double(ind.LSTF(2)-ind.LSTF(1))+1;

% Setup the measurement plots
[hSF,hCon,hEVM] = vhtTxSetupPlots(cfgVHT);

rmsEVM = zeros(numPackets,1);
pktOffsetStore = zeros(numPackets,1);

rng(savedState); % Restore random state

pktNum = 0;
searchOffset = 0; % Start at first sample (no offset)
while (searchOffset+minPktLen)<=rxWaveformLength
    % Packet detect
    pktOffset = wlanPacketDetect(rxWaveform,cfgVHT.ChannelBandwidth, ...
        searchOffset,0.9);
    % Packet offset from start of waveform
    pktOffset = searchOffset+pktOffset;
    % If no packet detected or offset outwith bounds of waveform then stop
    if isempty(pktOffset) || (pktOffset<0) || ...
            ((pktOffset+ind.LSIG(2))>rxWaveformLength)
        break;
    end

    % Extract non-HT fields and perform coarse frequency offset correction
    % to allow for reliable symbol timing
    nonht = rxWaveform(pktOffset+(ind.LSTF(1):ind.LSIG(2)),:);
    coarsefreqOff = wlanCoarseCFOEstimate(nonht,cfgVHT.ChannelBandwidth);
    nonht = helperFrequencyOffset(nonht,fs,-coarsefreqOff);

    % Determine offset between the expected start of L-LTF and actual start
    % of L-LTF
    lltfOffset = wlanSymbolTimingEstimate(nonht,cfgVHT.ChannelBandwidth);
    % Determine packet offset
    pktOffset = pktOffset+lltfOffset;
    % If offset is without bounds of waveform  skip samples and continue
    % searching within remainder of the waveform
    if (pktOffset<0) || ((pktOffset+pktLength)>rxWaveformLength)
        searchOffset = pktOffset+double(ind.LSTF(2))+1;
        continue;
    end

    % Timing synchronization complete; extract the detected packet
    rxPacket = rxWaveform(pktOffset+(1:pktLength),:);
    pktNum = pktNum+1;
    disp(['  Packet ' num2str(pktNum) ' at index: ' num2str(pktOffset+1)]);

    % Apply coarse frequency correction to the extracted packet
    rxPacket = helperFrequencyOffset(rxPacket,fs,-coarsefreqOff);

    % Perform fine frequency offset correction on the extracted packet
    lltf = rxPacket(ind.LLTF(1):ind.LLTF(2),:); % Extract L-LTF
    fineFreqOff = wlanFineCFOEstimate(lltf,cfgVHT.ChannelBandwidth);
    rxPacket = helperFrequencyOffset(rxPacket,fs,-fineFreqOff);

    % Estimate noise power in VHT fields
    lltf = rxPacket(ind.LLTF(1):ind.LLTF(2),:);
    demodLLTF = wlanLLTFDemodulate(lltf,cfgVHT);
    noiseVarVHT = helperNoiseEstimate(demodLLTF,cfgVHT.ChannelBandwidth, ...
        cfgVHT.NumSpaceTimeStreams);

    % Extract VHT-LTF samples, demodulate and perform channel estimation
    vhtltf = rxPacket(ind.VHTLTF(1):ind.VHTLTF(2),:);
    vhtltfDemod = wlanVHTLTFDemodulate(vhtltf,cfgVHT);
    chanEst = wlanVHTLTFChannelEstimate(vhtltfDemod,cfgVHT);

    % Spectral flatness measurement
    vhtTxSpectralFlatnessMeasurement(chanEst,cfgVHT,pktNum,hSF);

    % Extract VHT Data samples and perform OFDM demodulation, equalization
    % and phase tracking
    vhtdata = rxPacket(ind.VHTData(1):ind.VHTData(2),:);
    [~,~,eqSym] = wlanVHTDataRecover(vhtdata,chanEst,noiseVarVHT, ...
                    cfgVHT,cfgRec);

    % Compute RMS EVM over all spatial streams for packet
    rmsEVM(pktNum) = EVMPerPkt(eqSym);
    fprintf('    RMS EVM: %2.2f%%, %2.2fdB\n', ...
        rmsEVM(pktNum),20*log10(rmsEVM(pktNum)/100));

    % Compute RMS EVM per subcarrier and spatial stream for the packet
    evmPerSC = EVMPerSC(eqSym); % Nst-by-1-by-Nss

    % Plot RMS EVM per subcarrier and equalized constellation
    vhtTxEVMConstellationPlots(eqSym,evmPerSC,cfgVHT,pktNum,hCon,hEVM);

    % Store the offset of each packet within the waveform
    pktOffsetStore(pktNum) = pktOffset;

    % Increment waveform offset and search remaining waveform for a packet
    searchOffset = pktOffset+pktLength+minPktLen;
end

if pktNum>0
fprintf('Average EVM for %d packets: %2.2f%%, %2.2fdB\n', ...
    pktNum,mean(rmsEVM(1:pktNum)),20*log10(mean(rmsEVM(1:pktNum))/100));
else
    disp('No complete packet detected');
end

startIdx = osf*(ind.VHTData(1)-1)+1;  % Upsampled start of VHT Data
endIdx = osf*ind.VHTData(2);          % Upsampled end of VHT Data
delay = grpdelay(decimationFilter,1); % Group delay of downsampling filter
idx = zeros(endIdx-startIdx+1,pktNum);
for i = 1:pktNum
    % Start of packet in txWaveform
    pktOffset = osf*pktOffsetStore(i)-delay;
    % Indices of VHT Data in txWaveform
    idx(:,i) = (pktOffset+(startIdx:endIdx));
end
gatedVHTData = txWaveform(idx(:),:);

helperSpectralMaskTest(gatedVHTData,fs,osf);