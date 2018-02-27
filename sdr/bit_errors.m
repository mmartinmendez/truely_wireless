function [Pe,errors,N_RecBits] = bit_errors(dI,dIrec,mode)
% [Pe,errors,N_RecBits] = symb_errors(dI,dIrec)
%
% Count bit errors for a 1D binary signal constellation
%%///////////////////////////////////////////////////////////////////////
%    dI = reference bits from transmitter as {0,1} values
% dIrec = received bits as {0,1} values
%  mode = 1 then input data bits are assumed to be {-1,1} values
%%///////////////////////////////////////////////////////////////////////
% Mark Wickert October 2010


if nargin == 3 & mode == 1
    % Do nothing to inputs if already in +/-1 levels
else
    % Translate {0,1} values to +/-1 values
    dI = 2*dI-1;
    dIrec = 2*dIrec-1;
end

trim = 1;
M = 1;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% I ==> I and Q ==> Q
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Remove filter delay/transient bits
dIrec = dIrec(trim:end);
d_len = length(dIrec);
% Trim transmit bits to match length of received bits
dI = dI(1:d_len);
% Count errors, but resolve data invert ambiquities
% Use a cross correlation approach to find the proper delay 
N = 100; % code alignment window
% xcorr over a length M data window and consider 2*10+1 total lags
[IcorrI,lags] = xcorr(dI(1:N),dIrec(1:N),20);
% Find correlation peak in abs() sense
[IcorrImax,IImax] = max(abs(IcorrI));
Iflag = 0;
Thresh = 0.8;
if IcorrImax/M >= Thresh*N
    Ilag = lags(IImax);
    Iflag = 1;
end
% Count errors on input I data for positive and negative lags. We
% will need to trim the Tx and Rx I/Q data accordingly so we have
% equal length records for error detecting. If Iflag/Qflag was
% never set we have a high error condition, so we set all errors as
% an indicator of a bad frame.
switch Iflag
    case 0
        errors = length(dIrec);
        N_RecBits = length(dIrec);
    case 1
        if Ilag <= 0
            % Manage I inversion
            errorsIa = sign(abs(dI(1:end-abs(Ilag)) - ...
                dIrec(abs(Ilag)+1:end)));
            errorsIb = sign(abs(-dI(1:end-abs(Ilag)) - ...
                dIrec(abs(Ilag)+1:end)));
            errors = min(sum(errorsIa),sum(errorsIb));
            N_RecBits = length(dI(1:end-abs(Ilag)));
        else
            % Manage I inversion
            errorsIa = sum(abs(dIrec(1:end-abs(Ilag)) -...
                dI(abs(Ilag)+1:end)));
            errorsIb = sum(abs(-dIrec(1:end-abs(Ilag)) -...
                dI(abs(Ilag)+1:end)));
            errors = min(sum(errorsIa),sum(errorsIb));
            N_RecBits = length(dI(abs(Ilag)+1:end));
        end
end

Pe = errors/N_RecBits;
my_label1 = sprintf('Bit Errors: %d',errors);
my_label2 = sprintf('Bits Total: %d',N_RecBits);
my_label3 = sprintf('       BEP: %2.2e',Pe);

disp(sprintf('/////////////////////////////////////////////////////////'))
disp(my_label1)
disp(my_label2)
disp(my_label3)
disp(sprintf('/////////////////////////////////////////////////////////'))
