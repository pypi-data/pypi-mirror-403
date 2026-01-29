import numpy as np
import psutil as psu
import astropy.units as u
from peegy.processing.system.progress import ParallelTqdm
from .. filters.eegFiltering import filt_filt_worker_ovs, filt_worker_ovs
import joblib


def filt_data(data: type(np.array) | None = None,
              b: type(np.array) | None = None,
              n_jobs=None,
              ch_per_block=None,
              onset_padding=True,
              mode='original',
              max_percentage_memory: float = 0.8):
    """
    This function will filter input data. Coefficients must arise from a FIR filter
    :param data: a mxn matrix, data is filter on their first dimension
    :param b: filter coefficients
    :param n_jobs: number of parallel tasks
    :param ch_per_block: number of columns to be filtered by each job
    :param onset_padding: whether to pad data at the beginning and the end of the first dimension. This minimizes
    the ringing effect of the filter
    :param mode: any of these {'original', 'full', 'valid'}. It determines the size of the convolved output
    :param max_percentage_memory: memory limit in percentage used to estimate parallel processing resources
    :return: filtered data (mxn numpy array)
    """
    b = b * u.dimensionless_unscaled
    pad_width = 0
    if onset_padding:
        # we do this to minimize ringing of filter
        pad_width = data.shape[0] // 8
        data = np.vstack((data[1:pad_width + 1, :][::-1], data, data[::-1, :][1:pad_width + 1]))
    filtered_data = data
    if not n_jobs:
        n_jobs = np.maximum(joblib.cpu_count(), 1)
    else:
        n_jobs = np.minimum(joblib.cpu_count(), n_jobs)

    padding_size = ((0, b.size - 1), *((0, 0),) * (filtered_data.ndim - 1))
    padding_value = (((0, 0),) * filtered_data.ndim)
    filtered_data = np.pad(filtered_data, padding_size,
                           'constant',
                           constant_values=padding_value)

    if not ch_per_block:
        _virtual_memory = psu.virtual_memory()
        ch_per_block = np.maximum(1, int(_virtual_memory.available * max_percentage_memory /
                                         (n_jobs * filtered_data.nbytes / filtered_data.shape[1])))
    ch_per_block = np.minimum(filtered_data.shape[1], ch_per_block)
    # print('filtering {:} channels per block'.format(ch_per_block))

    if mode == 'full':
        samples_delay = 0
        samples_delay_end = 0
    if mode == 'original':
        # compensates for delay assuming that the FIR filter coefficients are symmetric
        samples_delay = (b.size - 1) // 2
        samples_delay_end = samples_delay
    if mode == 'valid':
        samples_delay = 0
        samples_delay_end = b.size - 1

    for _bl in np.arange((np.ceil(filtered_data.shape[1]) / ch_per_block)):
        pos_ini = int(_bl * ch_per_block)
        pos_end = int(np.minimum((_bl + 1) * ch_per_block, filtered_data.shape[1]))
        _b_size = pos_end - pos_ini
        _ch_per_thread = int(np.ceil(float(_b_size) / n_jobs))
        _n_jobs = int(np.minimum(n_jobs, np.ceil(float(_b_size) / _ch_per_thread)))
        sub_pos_ini = []
        sub_pos_end = []
        for _t in range(_n_jobs):
            sub_pos_ini.append(int(pos_ini + _ch_per_thread * _t))
            sub_pos_end.append(int(np.minimum(pos_end, pos_ini + _ch_per_thread * (_t + 1))))

        ParallelTqdm(total=_n_jobs,
                     desc='Parallel filtering/worker',
                     n_jobs=_n_jobs,
                     mmap_mode='w+',
                     backend='threading')(
            joblib.delayed(filt_worker_ovs)(filtered_data, sub_pos_ini[_i], sub_pos_end[_i], b) for
            _i in range(_n_jobs))
        # print('Filtered channels: {:} to {:}'.format(pos_ini, pos_end - 1))

    return filtered_data[pad_width + samples_delay:
                         filtered_data.shape[0] - pad_width - samples_delay_end, :]


def filt_filt_data(data: type(np.array) | None = None,
                   b: type(np.array) | None = None,
                   n_jobs=None,
                   ch_per_block=None,
                   onset_padding=True):
    """
    This function will filter input data using a zero group-delay technique. Coefficients must arise from a FIR filter
    :param data: a mxn matrix, data is filter on their first dimension
    :param b: filter coefficients
    :param n_jobs: number of parallel tasks
    :param ch_per_block: number of columns to be filtered by each job
    :param onset_padding: whether to pad data at the beginning and the end of the first dimension. This minimizes
    the ringing effect of the filter.
    :return: filtered data (mxn numpy array)
    """
    b = b * u.dimensionless_unscaled
    pad_width = 0
    if onset_padding:
        # we do this to minimize ringing of filter
        pad_width = data.shape[0] // 4
        data = np.vstack((data[1:pad_width + 1, :][::-1], data, data[::-1, :][1:pad_width + 1]))
    filtered_data = data
    if not n_jobs:
        n_jobs = np.maximum(joblib.cpu_count(), 1)
    else:
        n_jobs = np.minimum(joblib.cpu_count(), n_jobs)
    if not ch_per_block:
        _virtual_memory = psu.virtual_memory()
        ch_per_block = np.maximum(1, int(_virtual_memory.available /
                                         (filtered_data.nbytes / filtered_data.shape[1]) * 0.1))
    ch_per_block = np.minimum(filtered_data.shape[1], ch_per_block)
    print('filtering {:} channels per block'.format(ch_per_block))

    for _bl in np.arange((np.ceil(filtered_data.shape[1]) / ch_per_block)):
        pos_ini = int(_bl * ch_per_block)
        pos_end = int(np.minimum((_bl + 1) * ch_per_block, filtered_data.shape[1]))
        _b_size = pos_end - pos_ini
        _ch_per_thread = int(np.ceil(float(_b_size) / n_jobs))
        _n_jobs = int(np.minimum(n_jobs, np.ceil(float(_b_size) / _ch_per_thread)))
        # print(('filtering {:} channels per job ({:} parallel jobs)'.format(_ch_per_thread, _n_jobs)))
        sub_pos_ini = []
        sub_pos_end = []
        for _t in range(_n_jobs):
            sub_pos_ini.append(int(pos_ini + _ch_per_thread * _t))
            sub_pos_end.append(int(np.minimum(pos_end, pos_ini + _ch_per_thread * (_t + 1))))

        ParallelTqdm(total=_n_jobs,
                     desc='Parallel filtering',
                     n_jobs=_n_jobs,
                     mmap_mode='w+',
                     backend='threading')(
            joblib.delayed(filt_filt_worker_ovs)(filtered_data, sub_pos_ini[_i], sub_pos_end[_i], b) for
            _i in range(_n_jobs))
        # print('Filtered channels: {:} to {:}'.format(pos_ini, pos_end - 1))
    return filtered_data[pad_width: filtered_data.shape[0] - pad_width, :]
