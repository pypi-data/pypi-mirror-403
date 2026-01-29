"""
.. _tut-acc-standard-vs-weighted-average-sim:

################################################
ACC standard vs. weighted average (Simulated)
################################################
This example simulates an ACC response and compares the use of standard with weighted average.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.pipe.detection import PeakDetectionTimeDomain
from peegy.processing.pipe.general import ReferenceData, FilterData, RegressOutEOG, ReSampling, AutoRemoveBadChannels
from peegy.processing.pipe.epochs import AverageEpochs, EpochData, SortEpochs
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.statistics import HotellingT2Test
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import astropy.units as u
import numpy as np

# %%
# Define analysis windows for peak detection
# -------------------------------------------
# First we define the time windows that would be used to detect time-domain peaks.


tw = np.array([TimePeakWindow(ini_time=50 * u.ms, end_ref='N1', label='P1', positive_peak=True),
               TimePeakWindow(ini_time=100 * u.ms, end_time=200 * u.ms, label='N1', positive_peak=False),
               TimePeakWindow(ini_ref='N1', end_time=300 * u.ms, label='P2', positive_peak=True)]
              )

# %%
# Define peak-to-peak and region-of-interest measures
# --------------------------------------------------------
# Next, we define the peak-to-peak measures we want to save. These are based on the peaks that would be searched within
# the time windows defined in the previous step.
# TimeROI defines generic time windows that would be used to compute different statistics requiring a specific window,
# for example, Hotelling T2 tests in the time-domain.


pm = np.array([PeakToPeakMeasure(ini_peak='N1', end_peak='P2')])
roi_windows = np.array([TimeROI(ini_time=100.0 * u.ms, end_time=250.0 * u.ms, label="itd_snr"),
                        TimeROI(ini_time=0.0 * u.ms, end_time=400.0 * u.ms, label="itd_snr")])


# %%
# Generating some data
# ------------------------
# Now we generate a target signal, in this example, and auditory N1-P2 (ACC) signal.

n_channels=32
fs = 512.0 * u.Hz
template_waveform, _ = aep(fs=fs)
event_times = np.arange(0, 100.0, 1.0) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           layout_file_name='biosemi32.lay',
                           snr=0.05,
                           include_eog_events=True,
                           include_non_stationary_noise_events=False,
                           noise_events_interval=9.0 * u.s,
                           noise_events_duration=3.0 * u.s,
                           noise_events_power_delta_db=25.0,
                           noise_seed=0,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='acc_standard_vs_weighted_test')
reader.run()

# %%
# Start the pipeline
# =======================
# Now we proceed with our basic processing pipeline
pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader, reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['down_sampled'] = ReSampling(pipeline['channel_cleaned'],
                                      new_sampling_rate=256. * u.Hz)
pipeline['eog_removed'] = RegressOutEOG(pipeline['down_sampled'],
                                        ref_channel_labels=['EOG1'])

pipeline['time_filtered_data'] = FilterData(pipeline['eog_removed'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=30.0 * u.Hz)
pipeline.run()

# %%
# Get Epochs
# -------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0)
pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          weight_data=True,
                                                          weight_across_epochs=False,
                                                          block_size=1)

# %%
# Compute HT2 statistics on weighted data
# ========================================
# Using the raw epochs we estimate Hotelling-T2 statistics using weighted averaging


pipeline['ht2_weighted_average'] = HotellingT2Test(pipeline['dss_time_epochs'],
                                                   roi_windows=roi_windows,
                                                   weight_data=True)

# %%
# Sort cleaned epochs
# ----------------------
# Data is now sorted base on their standard deviation (or RMS)

pipeline['sorted_dss_epochs'] = SortEpochs(pipeline['dss_time_epochs'])
pipeline.run()

# %%
# Compute average responses
# ----------------------------
# We compute weighted average on sorted epochs


pipeline['weighted_time_average'] = AverageEpochs(pipeline['sorted_dss_epochs'],
                                                  weight_across_epochs=False,
                                                  weighted_average=True,
                                                  roi_windows=roi_windows)

pipeline.run()

# %%
# Detect peaks
# ---------------
# Using the average data, we proceed detecting peaks


pipeline['peak_detection_weighted_ave'] = PeakDetectionTimeDomain(pipeline['weighted_time_average'],
                                                                  time_peak_windows=tw,
                                                                  peak_to_peak_measures=pm)

# %%
# Show some waveforms
# ----------------------


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['peak_detection_weighted_ave'],
                                                   topographic_channels=np.array(['C4', 'CP2']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   user_naming_rule='_weighted_time_average',
                                                   return_figures=True)
pipeline.run()


# %%
# Compute HT2 statistics on standard unweighted data
# ==================================================
# Using the raw epochs we estimate Hotelling-T2 statistics using standard averaging


pipeline['ht2_standard_average'] = HotellingT2Test(pipeline['dss_time_epochs'],
                                                   roi_windows=roi_windows,
                                                   weight_data=True)
pipeline.run()

# %%
# Compute average responses
# -------------------------
# We compute standard average

pipeline['standard_time_average'] = AverageEpochs(pipeline['time_epochs'],
                                                  roi_windows=roi_windows,
                                                  weighted_average=False)

pipeline.run()


# %%
# Detect peaks
# ------------
# Using the average data, we proceed detecting peaks


pipeline['peak_detection_standard_ave'] = PeakDetectionTimeDomain(pipeline['standard_time_average'],
                                                                  time_peak_windows=tw,
                                                                  peak_to_peak_measures=pm)

# %%
# Show some waveforms
# -------------------

pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['peak_detection_standard_ave'],
                                                   topographic_channels=np.array(['C4', 'CP2']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   return_figures=True,
                                                   user_naming_rule='_standard_time_average')

pipeline['plotter'] = PlotWaveforms(pipeline['peak_detection_standard_ave'],
                                    overlay=[pipeline['peak_detection_weighted_ave']],
                                    plot_x_lim=[0, 0.8],
                                    return_figures=True,
                                    user_naming_rule='_standard_vs_w_average')

pipeline.run()

# %%
# Get generated data and save to database
# =======================================
# Now we save our data to a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}
database_path = reader.input_node.paths.test_path.joinpath('acc_standard_vs_weighted_test_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['peak_detection_standard_ave'],
                                                      pipeline['peak_detection_weighted_ave'],
                                                      pipeline['ht2_standard_average'],
                                                      pipeline['ht2_weighted_average']])
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
