import numpy as np
from peegy.processing.tools.filters.resampling import eeg_resampling
import matplotlib.pyplot as plt
import astropy.units as u
import matplotlib
from scipy.signal import resample
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')

__author__ = 'jundurraga-ucl'


fs = 500.0 * u.Hz
f_s = 25.0 * u.Hz
n_o = fs.value * 11
t = np.arange(0, n_o) / fs
y1 = np.sin(2 * np.pi * u.rad * f_s * t + np.pi * u.rad / 2) * u.uV
y2 = np.sin(2 * np.pi * u.rad * 5 * f_s * t) * u.uV
y = np.tile(np.array(y1 + y2) + 0e6 + 0 * np.random.random(t.shape), (4, 1)).T * u.uV
new_fs = 250 * u.Hz
y[3 * y.shape[0]//4::, :] = 0

yf = np.fft.fft(y, axis=0)
freq = np.arange(len(yf)) * fs / len(yf)
yc, factor = eeg_resampling(x=y.copy(), new_fs=new_fs, fs=fs, blocks=8)

new_fs = fs * factor
new_time = np.arange(0, yc.shape[0]) / new_fs
plt.plot(t, y[:, 0], label='original', color='b')
plt.plot(t, y[:, 0], 'bo')
plt.plot(t, y1, label='h1')
plt.plot(t, y2, label='h2')
plt.plot(np.squeeze(new_time), yc[:, 0], 'r', label='Resampled_1')
plt.plot(np.squeeze(new_time), yc[:, 0], 'rv', label=None)

resampled_scipy = resample(y, new_time.size, t=None, axis=0)
plt.plot(np.squeeze(new_time), resampled_scipy[:, 0], 'g', label='resampled-scipy')
plt.plot(np.squeeze(new_time), resampled_scipy[:, 0], 'gv', label=None)
plt.legend()
plt.show()
plt.show()

freq_1 = np.arange(0, y.shape[0]) * fs / y.shape[0]
yfft1 = 2 * np.abs(np.fft.fft(y, axis=0)) / y.shape[0]
freq_2 = np.arange(0, yc.shape[0]) * new_fs / yc.shape[0]
yfft2 = 2 * np.abs(np.fft.fft(yc, axis=0)) / yc.shape[0]
freq_4 = np.arange(0, resampled_scipy.shape[0]) * new_fs / resampled_scipy.shape[0]
yfft4 = 2 * np.abs(np.fft.fft(resampled_scipy, axis=0)) / resampled_scipy.shape[0]

plt.figure()
plt.plot(freq_1, yfft1[:, 0], label='original')
plt.plot(freq_2, yfft2[:, 0], label='original-m1')
plt.plot(freq_4, yfft4[:, 0], label='scipy')
plt.legend()
plt.xlim([0, new_fs.value / 2])
plt.show()
