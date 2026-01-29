"""
.. _tut-abr-sim:

##################################
ABR peak detection (Simulated)
##################################

This example simulates an auditory brainstem response, detect peaks, and save results to a database.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')

from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.detection import PeakDetectionTimeDomain
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.pipe.general import ReferenceData, FilterData, RegressOutEOG, ReSampling
from peegy.processing.pipe.epochs import AverageEpochs, EpochData, RejectEpochs
from peegy.processing.pipe.plot import PlotWaveforms
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.statistics import HotellingT2Test
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import abr
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
from peegy.io.storage.data_storage_reading_tools import sqlite_tables_to_pandas, sqlite_waveforms_to_pandas
from peegy.io.storage.plot_tools import plot_time_frequency_responses
import os
import astropy.units as u
import numpy as np


# %%
# Time windows
# ======================
# Time windows are used to define where to look for different peaks

tw = np.array([
    TimePeakWindow(ini_time=4e-3 * u.s, end_time=6e-3 * u.s, label='V', positive_peak=True),
    TimePeakWindow(ini_ref='V', end_time=12e-3 * u.s, label='N_V', positive_peak=False),
    TimePeakWindow(ini_time=4e-3 * u.s, end_ref='V', label='N_III', positive_peak=False),
    TimePeakWindow(ini_time=3e-3 * u.s, end_ref='N_III', label='III', positive_peak=True),
    TimePeakWindow(ini_time=2e-3 * u.s, end_ref='III', label='N_II', positive_peak=False),
    TimePeakWindow(ini_time=2e-3 * u.s, end_ref='N_II', label='II', positive_peak=True),
    TimePeakWindow(ini_time=1e-3 * u.s, end_ref='II', label='N_I', positive_peak=False),
    TimePeakWindow(ini_time=1e-3 * u.s, end_ref='N_I', label='I', positive_peak=True),
])
# %%
# Peak-to-peak Measures
# ==========================
# Peak-to-peak measures are defined based on the labels of the TimePeaks defined above.


pm = np.array([
    PeakToPeakMeasure(ini_peak='I', end_peak='N_I'),
    PeakToPeakMeasure(ini_peak='II', end_peak='N_II'),
    PeakToPeakMeasure(ini_peak='III', end_peak='N_III'),
    PeakToPeakMeasure(ini_peak='V', end_peak='N_V'),
    PeakToPeakMeasure(ini_peak='III', end_peak='V')])

# %%
# Time regions of interest
# ============================
# TimeROI are defined as time regions where different measures will be performed, e.g. SNR measure or statistical
# measures


roi_windows = np.array([TimeROI(ini_time=1e-3 * u.s, end_time=1./47 * u.s, label="abr_snr")])

# %%
# Generating some data
# ============================
# First we generate a target signal, in this example, and auditory brainstem response (ABR) with a target final SNR,
# this is, the expected SNR when all trials or epochs are averaged.


fs = 8192.0 * u.Hz
template_waveform, _ = abr(fs=fs, time_length=0.02 * u.s)
n_channels = 4
event_times = np.arange(0, 240.0, 1./47.0) * u.s
n_trials = event_times.shape[0]
desired_snr_db = 6
snr = 10 ** (desired_snr_db / 10) / n_trials

reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.array([0.001, 1, 1, 1])),
                           eog_mixing_matrix=np.diag(np.array([0, -1, 1, 1])),
                           snr=np.array([0.001 ** 2 * snr, snr, snr, snr]),
                           noise_attenuation=3,
                           include_eog_events=True,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='abr_test')
reader.run()
# %%
# Processing pipe line
# ========================
# First we initialize and populate the pipeline


pipeline = PipePool()

pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['CH_0'],
                                       invert_polarity=False)
pipeline['channel_cleaned'] = RegressOutEOG(pipeline['referenced'],
                                            ref_channel_labels=['EOG1'],
                                            method='template')
pipeline['time_filtered_data'] = FilterData(pipeline['channel_cleaned'],
                                            high_pass=47.0 * u.Hz,
                                            low_pass=None)
pipeline.run()
# %%
# Lets see the output of the filter
# --------------------------------------
# First we generate a target signal, in this example, and auditory brainstem response (ABR).

pipeline['time_filtered_data'].plot(plot_input=True,
                                    plot_output=True,
                                    interactive=False,
                                    show_events=False)

# %%
# Processing pipe continue
# ------------------------------
# First we generate a target signal, in this example, and auditory brainstem response (ABR).


pipeline['time_epochs_filtered'] = EpochData(pipeline['time_filtered_data'],
                                             event_code=1.0,
                                             post_stimulus_interval=20 * u.ms,
                                             base_line_correction=False)
pipeline['time_epochs'] = RejectEpochs(pipeline['time_epochs_filtered'],
                                       rejection_threshold=100 * u.uV,
                                       rejection_percentage=0.1,
                                       std_threshold=3.0)
pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          plot_x_lim=[0, 0.012],
                                                          sf_components=np.arange(0, 1),
                                                          return_figures=True)
pipeline['ht2'] = HotellingT2Test(pipeline['time_epochs'],
                                  roi_windows=roi_windows,
                                  block_time=1e-3 * u.s)

pipeline['ht2dss'] = HotellingT2Test(pipeline['dss_time_epochs'],
                                     roi_windows=roi_windows,
                                     block_time=1e-3 * u.s)

pipeline['time_average'] = AverageEpochs(pipeline['time_epochs'],
                                         roi_windows=roi_windows)
pipeline['time_average_dss'] = AverageEpochs(pipeline['dss_time_epochs'],
                                             roi_windows=roi_windows)
# we up-sample to improve time peak detection
pipeline['up_sampled'] = ReSampling(pipeline['time_average'],
                                    new_sampling_rate=fs * 2)

pipeline['up_sampled_dss'] = ReSampling(pipeline['time_average_dss'],
                                        new_sampling_rate=fs * 2)
pipeline.run()
pipeline['up_sampled_dss'].plot(plot_input=True,
                                plot_output=True,
                                ch_to_plot=['CH_0', 'CH_1', 'CH_2'],
                                interactive=False)
pipeline['up_sampled_peaks'] = PeakDetectionTimeDomain(pipeline['up_sampled'],
                                                       time_peak_windows=tw,
                                                       peak_to_peak_measures=pm)
pipeline['up_sampled_peaks_dss'] = PeakDetectionTimeDomain(pipeline['up_sampled_dss'],
                                                           time_peak_windows=tw,
                                                           peak_to_peak_measures=pm)
pipeline['plotter'] = PlotWaveforms(pipeline['up_sampled_peaks'],
                                    overlay=[pipeline['up_sampled_peaks_dss']],
                                    plot_x_lim=[0, 0.012],
                                    return_figures=True)
pipeline.run()

# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ABR'}
database_path = reader.input_node.paths.test_path.joinpath('abr_test_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['ht2'],
                                                      pipeline['ht2dss'],
                                                      pipeline['up_sampled_peaks'],
                                                      pipeline['up_sampled_dss']],
                                      include_waveforms=True,
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)

# %%
# Read the saved data and show the tables
# ------------------------------------------
df = sqlite_tables_to_pandas(database_path=database_path,
                             tables=['peaks_time',
                                     'f_test_time',
                                     'amplitudes'])
print(df.peaks_time[['anonymous_name', 'channel', 'peak_label', 'x', 'x_unit']])
print(df.f_test_time[['anonymous_name', 'channel', 'f', 'p_value']])
print(df.amplitudes[['anonymous_name', 'channel', 'amp_label', 'amp', 'amp_unit']])

# Read waveforms from generated database and plot them
# ---------------------------------------------------------
df_waves = sqlite_waveforms_to_pandas(database_path=database_path,
                                      group_factors=['Type', 'data_source', 'channel'],
                                      channels=['CH_1', 'CH_2', 'CH_3'])
df_waves = df_waves.loc[df_waves['data_source'] == 'up_sampled_dss']
fig_out = plot_time_frequency_responses(dataframe=df_waves,
                                        rows_by='Type',
                                        cols_by='channel',
                                        title_by='col')
