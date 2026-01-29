from peegy.processing.tools.epochs_processing_tools import et_subtract_oeg_template
from peegy.processing.tools.multiprocessing.multiprocessesing_filter import filt_data
import numpy as np
from scipy.io import loadmat
import os
import astropy.units as u
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')


_directory = os.path.dirname(os.path.abspath(__file__))
data_path = _directory + os.sep + 'test_data' + os.sep + 'eog_blinks_valderrama_et_al_2018.mat'
data_structure = loadmat(data_path)
fs = float(data_structure['fs'].squeeze()) * u.Hz
data = data_structure['y'] * u.uV

# remove artefacts
clean_data, fig_results, template, z, eog_events = et_subtract_oeg_template(data=data,
                                                                            idx_ref=np.array([0]),
                                                                            fs=fs,
                                                                            n_iterations=15,
                                                                            plot_results=True,
                                                                            high_pass=None,
                                                                            low_pass=20 * u.Hz,
                                                                            template_width=1.4 * u.s,
                                                                            kernel_bandwidth=0.15,
                                                                            use_initial_template=True
                                                                            )
fig_results[0].show()

# SNR estimate
length = template.size
norm_2 = filt_data(data ** 2, np.ones(template.shape[0]), onset_padding=False, mode='valid')
z_norm_2 = z ** 2 / norm_2
z_norm_k2 = z_norm_2[eog_events + length - 1].value
snr = 10 * np.log10(np.mean(z_norm_k2 / (1 - z_norm_k2)))
print('SNR: {:}'.format(np.round(snr, decimals=2)))
