import numpy as np


def get_local_minima(x: type(np.array) | None = None):
    _minima_idx = np.arange(x.shape[0])[np.r_[True, x[1:] < x[:-1]] & np.r_[x[:-1] < x[1:], True]]
    return x[_minima_idx], _minima_idx


def get_local_maxima(x: type(np.array) | None = None):
    _maxima_idx = np.arange(x.shape[0])[np.r_[True, x[1:] > x[:-1]] & np.r_[x[:-1] > x[1:], True]]
    return x[_maxima_idx], _maxima_idx
