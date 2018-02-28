#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 15:20:05 2018

@author: myth
"""
import rtlsdr
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal
from scipy.io.wavfile import write


fs = 1e6 # sampling frequency
f_int = 100.4e6 
f_off = 240000 #offset to account for dc spike
fc = f_int-f_off
N = 4194304
gain = 25.6

sdr = rtlsdr.RtlSdr()
sdr.sample_rate = fs
sdr.center_freq = fc

sdr.gain = 30.7

x = sdr.read_samples(N)

sample = np.array(x).astype("complex64")

# power spectral diagram with shift
plt.psd(sample, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB))')
plt.savefig("psd diagram.pdf", bbox_inches='tight', pad_inches=0.5)
plt.close()

# spectrogram with the shift from the center frequency
plt.specgram(sample, NFFT=2048, Fs=fs)
plt.title("x")
plt.ylim(-fs/2,fs/2)
plt.savefig("spec diagram", bbox_inches="tight", pad_inches=0.5)
plt.close()

f_shift = np.exp(-1.0j*2.0*np.pi*f_off/fs*np.arange(len(sample)))
sample2 = sample*f_shift

# power spectral diagram with shift
plt.psd(sample2, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB))')
plt.savefig("psd diagram 2.pdf", bbox_inches='tight', pad_inches=0.5)
plt.close()

# spectrogram with the shift corrected to the center
plt.specgram(sample2, NFFT=2048, Fs=fs)
plt.title("x")
plt.ylim(-fs/2,fs/2)
plt.xlim(0, len(sample2)/fs)
plt.savefig("spec diagram 2", bbox_inches="tight", pad_inches=0.5)
plt.close()

# run the acquired data through a LPF using windowed FIR design
# for this the cut-off frequency B1 need to be found
# taps = 64

bw = 200000
taps = 64
B1 = fs/4

lpf = signal.firwin(taps,B1,fs=fs)
filtered = np.convolve(sample2,lpf) #apply filter to the signal

# decimate the output from the filter, plot psd and comment (downsampling)
rate = int(fs/bw)
sample3 = filtered[0::rate]
fs2 = fs/rate

# power spectral diagram with shift
plt.psd(sample3, NFFT=2048, Fs=fs2, color="blue")
plt.xlabel('Frequency (MHz)')
plt.ylabel('Relative power (dB))')
plt.savefig("psd of filtered downsampled signal.pdf", bbox_inches='tight', pad_inches=0.5)
plt.close()

plt.specgram(sample3, NFFT=2048, Fs=fs2)  
plt.title("sample 3")  
plt.ylim(-fs2/2, fs2/2)  
plt.xlim(0,len(sample3)/fs2)  
plt.ticklabel_format(style='plain', axis='y' )  
plt.savefig("spectrogram of filtered downsampled signal.pdf", bbox_inches='tight', pad_inches=0.5)  
plt.close()  

# send the subsequent signal through a discriminator
# plot the spectrum of the signal
# identify features in the plot and label

y = sample3[1:]*np.conj(sample3[:-1])
sample4 = np.angle(y)

plt.specgram(sample4, NFFT=2048, Fs=fs2)  
plt.title("sample 4")  
plt.ylim(-fs2/2, fs2/2)  
plt.xlim(0,len(sample4)/fs2)  
plt.ticklabel_format(style='plain', axis='y' )  
plt.savefig("spectrogram of filtered downsampled signal 2.pdf", bbox_inches='tight', pad_inches=0.5)  
plt.close() 

plt.psd(sample4, NFFT=2048, Fs=fs2, color="blue")  
plt.title("sample 4")  
plt.axvspan(0,             15000,         color="blue", alpha=0.2)  
plt.axvspan(19000-500,     19000+500,     color="red", alpha=0.4)  
plt.axvspan(19000*2-15000, 19000*2+15000, color="yellow", alpha=0.2)  
plt.axvspan(19000*3-1500,  19000*3+1500,  color="green", alpha=0.2)  
plt.ticklabel_format(style='plain', axis='y' )  
plt.savefig("Discriminated signal.pdf", bbox_inches='tight', pad_inches=0.5)  
plt.close()  

# design second LPF with B2
# down sample to 48ksps and save the vector as a .wav file

bw2 = 200000
taps2 = 64
B2 = fs2/4

lpf2 = signal.firwin(taps2,B2,fs=fs2)
filtered2 = np.convolve(sample4,lpf2)

rate2 = int(fs2/bw2)
sample5 = filtered2[0::rate2]
fs3 = fs2/rate2

M = 5
sample5 = sample5[0::M]

audio_freq = 44100.0  
dec_audio = int(fs2/audio_freq)  
Fs_audio = fs2 / dec_audio

x7 = signal.decimate(sample5, dec_audio)  

# Scale audio to adjust volume
x7 *= 10000 / np.max(np.abs(x7))  

scaled = np.int16(x7/np.max(np.abs(x7)) * 32767)
write('fm_audio.wav', 44100, scaled)
#print('Saved as binary wav file with (I,Q)<=>(L,R)')
