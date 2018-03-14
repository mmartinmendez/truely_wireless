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