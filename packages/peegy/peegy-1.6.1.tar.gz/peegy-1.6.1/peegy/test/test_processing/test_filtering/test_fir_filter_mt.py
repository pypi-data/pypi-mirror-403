import numpy as np
from peegy.processing.tools.filters import eegFiltering as eegf
import scipy.signal as signal
import time
import matplotlib.pyplot as plt
import peegy.processing.tools.multiprocessing.multiprocessesing_filter as mp
import astropy.units as u
# Enable below for interactive backend
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')

fs = 1000.0 * u.Hz
f1 = 10.0 * u.Hz
f2 = 43.0 * u.Hz
low_pass = 16.115 * u.Hz
high_pass = 3.885 * u.Hz
low = 2 * low_pass / fs
high = 2 * high_pass / fs
t = np.arange(0, 70000) / fs
s = np.sin(2 * np.pi * u.rad * f1 * t) + np.sin(2 * np.pi * u.rad * f2 * t)
data = np.tile(s, [10, 1]).T

_b_l_1 = eegf.bandpass_fir_win(fs=fs, high_pass=high_pass, low_pass=low_pass, transition_width=1 * u.Hz,
                               filt_filt_cutoff=False)
n_passes = 2
_b_l_2 = eegf.bandpass_fir_win(fs=fs, high_pass=high_pass, low_pass=low_pass, transition_width=1 * u.Hz,
                               filt_filt_cutoff=True, n_passes=n_passes)
w, h_1 = signal.freqz(_b_l_1, worN=36000)
w, h_2 = signal.freqz(_b_l_2, worN=36000)
plt.plot((w/np.pi)*fs*0.5, 20 * np.log10(np.abs(h_2)), linewidth=2)
plt.plot((w/np.pi)*fs*0.5, 20 * np.log10(np.abs(h_2) ** n_passes), linewidth=2)
plt.xlabel('Frequency (Hz)')
plt.show()

_data = data.copy()
time1 = time.time()
filtered_data_1 = mp.filt_data(_data, _b_l_2)
print(('multiprocessing filter took %f [ms]' % ((time.time()-time1) * 1000.0)))


_data = data.copy()
time1 = time.time()
filtered_data_2 = eegf.filt_worker_ovs(data=_data, pos_ini=0, pos_end=-1, b=_b_l_2)
print(('Overlap save filter took %f [ms]' % ((time.time()-time1) * 1000.0)))

_data = data.copy()
time1 = time.time()
filtered_data_3 = mp.filt_filt_data(data=_data, b=_b_l_2)
print(('Filtfilt filter took %f [ms]' % ((time.time()-time1) * 1000.0)))

_data = data.copy()
time1 = time.time()
filtered_data_4 = mp.filt_data(data=_data, b=_b_l_2, onset_padding=False)
print(('Filtfilt filter took %f [ms]' % ((time.time()-time1) * 1000.0)))


_data = data.copy()
time1 = time.time()
filtered_signal_standard = signal.lfilter(_b_l_2, [1], _data, axis=0)
print(('Standard filter took %f [ms]' % ((time.time()-time1) * 1000.0)))

plt.plot(t, data[:, 0], label='unfiltered')
plt.plot(t, filtered_data_1[:, 0], label='parallel filt ovs')
plt.plot(t, filtered_data_2[:, 0], label='filt ovs')
plt.plot(t, filtered_data_3[:, 0], label='filtfilt')
plt.plot(t, filtered_data_4[:, 0], label='filt no padding')
plt.plot(t, filtered_signal_standard[:, 0], label='scipy filt')
plt.legend()
plt.show()
