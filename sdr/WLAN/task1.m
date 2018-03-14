

useSDR = false;         % For transmitting set to true
saveToFile = false;     % To write baseband to a file set to true


SSID = 'TEST_BEACON';   % Network SSID
beaconInterval = 100;   % In Time units (TU) 1TU->1024 microseconds
band = 5;               % Band, 5 or 2.4 GHz
chNum = 52;             % Channel number, corresponds to 5260MHz

% Generate Beacon frame
[mpduBits,fc] = helperGenerateBeaconFrame(chNum, band, beaconInterval, SSID);

cfgNonHT = wlanNonHTConfig;              % Create a wlanNonHTConfig object
cfgNonHT.PSDULength = numel(mpduBits)/8; % Set the PSDU length in bits

% The idle time is the length in seconds of an idle period after each
% generated packet. The idle time is set to the beacon interval.
txWaveform = wlanWaveformGenerator(mpduBits, cfgNonHT, 'IdleTime', beaconInterval*1024e-6);
Rs = wlanSampleRate(cfgNonHT);           % Get the input sampling rate

if saveToFile
    % The waveform is stored in a baseband file
    BBW = comm.BasebandFileWriter('nonHTBeaconPacket.bb', Rs, fc); %#ok<UNRCH>
    BBW(txWaveform);
    release(BBW);
end

if useSDR
    tx = sdrtx('ZedBoard and FMCOMMS2/3/4'); %#ok<UNRCH>
    tx.ShowAdvancedProperties = true;
    tx.BypassUserLogic = true;
    osf = 2; % OverSampling factor
    tx.BasebandSampleRate = Rs*osf;
    % The center frequency is set to the corresponding channel number
    tx.CenterFrequency = fc;
end

if useSDR
    % Set transmit gain (0,-10,-20)
    tx.Gain = 0;  %#ok<UNRCH>
    % Resample transmit waveform
    txWaveform = resample(txWaveform, osf, 1);
    % Transmit over-the-air
    transmitRepeat(tx, txWaveform);
end