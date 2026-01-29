__author__ = 'jundurraga-ucl'
import numpy as np
import peegy.processing.tools.filters.eegFiltering as ep
import matplotlib.pyplot as plt
from astropy import units as u

fs = 44100.0 * u.Hz
t = np.arange(0, 5.5, 1/fs.value) * u.s
y = np.tile(np.array(np.sin(2*np.pi*u.rad * 50 * u.Hz * t)) + np.random.random(t.shape), (4, 1)).T * u.uV

yf = np.fft.fft(y, axis=0)
freq = np.arange(len(yf)) * fs / len(yf)
yc = ep.eeg_notch_filter(x=y, f=[50 * u.Hz, 100 * u.Hz], f_range=5.0 * u.Hz, fs=fs, blocks=8)
plt.plot(t, y)
plt.plot(t, np.squeeze(yc), 'r')
plt.show()
ycf = np.fft.fft(yc, axis=0)
plt.plot(freq, np.abs(yf))
plt.plot(freq, np.abs(ycf), 'r')
plt.show()
