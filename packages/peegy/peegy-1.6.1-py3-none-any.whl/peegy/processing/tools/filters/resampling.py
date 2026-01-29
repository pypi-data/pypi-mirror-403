import numpy
import numpy as np
import multiprocessing
import pyfftw
import astropy.units as u
from tqdm import tqdm
from peegy.tools.units.unit_tools import set_default_unit
from .. multiprocessing.multiprocessesing_filter import filt_data
from .. filters.eegFiltering import bandpass_fir_win

__author__ = 'jundurraga'


def eeg_resampling(x: np.array(u.Quantity) = np.array([]),
                   new_fs: type(u.Quantity) | None = None,
                   fs: type(u.Quantity) | None = None,
                   blocks=8,
                   padding: bool = True,
                   padding_width: int | None = None) -> np.array:
    x = set_default_unit(x, u.dimensionless_unscaled)
    factor = new_fs / fs
    if factor == 1.0:
        return x, factor
    n_samples = x.shape[0]
    if padding:
        if factor < 1.0:
            _b = bandpass_fir_win(high_pass=None,
                                  low_pass=new_fs / 2 * (1 - 0.1),
                                  fs=fs,
                                  transition_width=new_fs / 2 * 0.1)
            _b = _b * u.dimensionless_unscaled
            # apply filter to avoid edge effects
            x = filt_data(data=x, b=_b)
        # padding is using to reduce ringing when down sampling in the frequency domain.
        # ensure that padding length is that so that the input fft size is a multiple of the output fft. This will
        # ensure that down-sampling multiples of fs will as desired
        if padding_width is None:
            padding_width = x.shape[0] // 4
        if factor < 1.0:
            step = np.ceil(1 / factor).astype(int)
        else:
            step = np.floor(factor).astype(int)

        nfft_points = int(np.ceil((x.shape[0] + padding_width) / step) * step)
        pad_width = nfft_points - x.shape[0]
        a1 = x[-1, :]
        a2 = x[0, :]
        padded_samples = (a2 - a1) * np.arange(pad_width)[:, None] / pad_width + a1
        x = np.vstack((x, padded_samples))
    blocks = np.minimum(x.shape[1], blocks)
    updated_nfft = int(x.shape[0] / fs * new_fs)
    xfilt = np.zeros((updated_nfft, x.shape[1]))
    for b in tqdm(np.arange((np.ceil(x.shape[1]) / blocks)), desc='Resampling'):
        pos_ini = int(b * blocks)
        pos_end = int(np.minimum((b + 1) * blocks, x.shape[1]) + 1)
        fft = pyfftw.builders.rfft(x[:, pos_ini:pos_end],
                                   overwrite_input=False,
                                   planner_effort='FFTW_ESTIMATE',
                                   axis=0,
                                   threads=multiprocessing.cpu_count())
        fft_data = fft()
        _fft_shifted = fft_data
        ifft = pyfftw.builders.irfft(_fft_shifted,
                                     n=updated_nfft,
                                     overwrite_input=False,
                                     planner_effort='FFTW_ESTIMATE',
                                     axis=0,
                                     threads=multiprocessing.cpu_count())
        sub_set = ifft()
        xfilt[:, pos_ini:pos_end] = sub_set
        if pos_end == x.shape[1]:
            break
    _scaling_factor = xfilt.shape[0] / x.shape[0]
    _ini = 0
    _end = int(n_samples * _scaling_factor)
    xfilt = xfilt[_ini: _end, :]
    return xfilt * _scaling_factor * x.unit, _scaling_factor
