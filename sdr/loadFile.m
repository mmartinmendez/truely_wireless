function y = loadFile(filename)
% y = loadFile('dump.bin')
%
% reads  complex samples from the rtlsdr file 
%
% SDR>rtl_sdr -s f_in_sps -f f_in_Hz -g gain_dB capture.bin
% SDR>rtl_sdr -s 2400000 -f 70000000 -g 25 capture70R1k.bin

fid = fopen('dump_1001.bin');
y = fread(fid,'uint8=>double');

y = y-127;
y = y(1:2:end) + i*y(2:2:end);

% plot_FFT_IQ(y,1,.002*2.4,100.4,100.400);

% simpleSA(y,2^14,2400);
simpleSA(y, 2^14, 2400,-80,50,'r');
% print -depsc -tiff capture.eps
