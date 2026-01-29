# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 10:55:37 2014

@author: jundurraga-ucl
"""
import numpy as np
import matplotlib.pyplot as plt
import pyfftw
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')

# create synthetic data
fs = 1000.0
nsamples = np.round(1 * fs).astype(int)
nchans = 5
ntrials = 1
noise_dim = 300  # dimensionality of noise
f1 = 40
time = np.arange(nsamples) / fs
source = np.expand_dims(np.sin(2 * np.pi * f1 * time), axis=1)
coeff = np.arange(1, nchans)
coeff = np.expand_dims(np.hstack((coeff, coeff)), 0)

s = source * coeff
s_std = np.std(s, axis=0)
s = np.tile(np.expand_dims(s, axis=2), (1, 1, ntrials))

data = s

fft = pyfftw.builders.rfft(
                s,
                overwrite_input=False,
                planner_effort="FFTW_ESTIMATE",
                axis=0,
                threads=1,
                n=s.shape[0],
            )
fft_y = fft()
psd = 2 * np.abs(fft_y) ** 2 / (s.shape[0] ** 2)
w_fft = fft_y * 2 / s.shape[0]
amp_from_psd = (2 * psd) ** 0.5
freq = np.arange(0, w_fft.shape[0]) * fs / s.shape[0]
plt.figure(121)
plt.plot(time, data[:, :, 0], label='time')
plt.figure(122)
plt.plot(freq, np.abs(w_fft[:, :, 0]), label='amp')
plt.plot(freq, np.abs(amp_from_psd[:, :, 0]), label='psd_derived_amp')
plt.legend()
plt.show(block=True)
