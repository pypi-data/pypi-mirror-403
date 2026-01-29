"""
.. _tut-acc-standard-pipeline-filters-sim:

#################################################
ACC Standard analysis - filter delay (Simulated)
#################################################

In this example we simulate an ACC response and use two filters, one with zero-phase compensation and normal filter
 output.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.general import FilterData, ReSampling, AutoRemoveBadChannels, ReferenceData, RegressOutEOG, \
    BaselineCorrection
from peegy.processing.pipe.epochs import EpochData, AverageEpochs
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.statistics import HotellingT2Test
from peegy.processing.pipe.detection import PeakDetectionTimeDomain
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import numpy as np
import astropy.units as u

# %%
# Time windows
# ============================
# Time windows are used to define where to look for different peaks


tw = np.array([TimePeakWindow(ini_time=50 * u.ms, end_ref='N1', label='P1', positive_peak=True,
                              exclude_channels=['GFP']),
               TimePeakWindow(ini_time=80 * u.ms, end_time=200 * u.ms, label='N1', positive_peak=False,
                              exclude_channels=['GFP']),
               TimePeakWindow(ini_ref='N1', end_time=300 * u.ms, label='P2', positive_peak=True,
                              exclude_channels=['GFP']),
               TimePeakWindow(ini_time=50 * u.ms, end_time=150 * u.ms, label='gfp1', positive_peak=True,
                              target_channels=['GFP']),
               TimePeakWindow(ini_time=150 * u.ms, end_time=500 * u.ms, label='gfp2', positive_peak=True,
                              target_channels=['GFP'])])

# %%
# Peak-to-peak Measures
# ============================
# Peak-to-peak measures are defined based on the labels of the TimePeaks defined above.


pm = np.array([PeakToPeakMeasure(ini_peak='N1', end_peak='P2')])

# %%
# Time regions of interest
# ============================
# TimeROI are defined as time regions where different measures will be performed, e.g. SNR measure or statistical
# measures


roi_windows = np.array(
    [TimeROI(ini_time=100.0 * u.ms, end_time=250.0 * u.ms, label="acc_snr"),
     TimeROI(ini_time=500.0 * u.ms, end_time=600.0 * u.ms, label="control")])

# %%
# Generate some data
# ===================
# First we generate some ACC data

n_channels=32
fs = 512.0 * u.Hz
template_waveform, _ = aep(fs=fs)
event_times = np.arange(0, 100.0, 1.0) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           layout_file_name='biosemi32.lay',
                           snr=0.1,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='acc_test_filters',
                           include_eog_events=True,
                           )
reader.run()

# %%
# Start the pipeline
# ============================
# Now we proceed with our basic processing pipeline


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline.referenced)
pipeline['down_sampled'] = ReSampling(pipeline.channel_cleaned,
                                      new_sampling_rate=256. * u.Hz)
pipeline['eog_removed'] = RegressOutEOG(pipeline.down_sampled,
                                        ref_channel_labels=['EOG1'])
pipeline.run()
# %%
# Show EOG removal Output
# ------------------------------------

pipeline.eog_removed.plot(plot_input=True,
                          plot_output=True,
                          ch_to_plot=['CP1', 'CP5', 'P7'],
                          interactive=False)

# %%
# Continue with the pipeline
# ------------------------------------

pipeline['time_filtered_data_1'] = FilterData(pipeline.eog_removed,
                                              high_pass=2.0 * u.Hz,
                                              low_pass=30.0 * u.Hz,
                                              ripple_db=60 * u.dB,
                                              zero_latency=False)
pipeline['time_filtered_data_2'] = FilterData(pipeline.eog_removed,
                                              high_pass=2.0 * u.Hz,
                                              low_pass=30.0 * u.Hz,
                                              ripple_db=60 * u.dB,
                                              zero_latency=True)

pipeline.run()

# %%
# Get Epochs
# ------------------------------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs_1'] = EpochData(pipeline.time_filtered_data_1,
                                      event_code=1.0)
pipeline['time_epochs_2'] = EpochData(pipeline.time_filtered_data_2,
                                      event_code=1.0)
pipeline.run()

pipeline['time_epochs_with_gfp_1'] = AppendGFPChannel(pipeline.time_epochs_1)
pipeline['time_epochs_with_gfp_2'] = AppendGFPChannel(pipeline.time_epochs_2)
pipeline.run()

# %%
# Base line correction
# ------------------------------------
# We correct the initial segment by removing the mean in the first 20 ms
pipeline['time_epochs_with_baseline_corrected_1'] = BaselineCorrection(
    pipeline.time_epochs_with_gfp_1,
    ini_time=0 * u.ms,
    end_time=20 * u.ms)

pipeline['time_epochs_with_baseline_corrected_2'] = BaselineCorrection(
    pipeline.time_epochs_with_gfp_2,
    ini_time=0 * u.ms,
    end_time=20 * u.ms)
pipeline.run()

# %%
# Compute HT2 statistics
# ------------------------------------
# Using the raw epochs we estimate Hotelling-T2 statistics


pipeline['ht2_1'] = HotellingT2Test(pipeline.time_epochs_with_baseline_corrected_1,
                                    roi_windows=roi_windows)
pipeline['ht2_2'] = HotellingT2Test(pipeline.time_epochs_with_baseline_corrected_2,
                                    roi_windows=roi_windows)
pipeline.run()

# %%
# Compute average responses
# ------------------------------------
# We compute weighted average on epochs with and without spatial filtering (DSS)


pipeline['time_average_normal_1'] = AverageEpochs(pipeline.time_epochs_with_baseline_corrected_1,
                                                  roi_windows=roi_windows,
                                                  weighted_average=True)
pipeline['time_average_normal_2'] = AverageEpochs(pipeline.time_epochs_with_baseline_corrected_2,
                                                  roi_windows=roi_windows,
                                                  weighted_average=True)
pipeline.run()

# %%
# Detect peaks
# ------------------------------------
# Using the average data, we proceed detecting peaks


pipeline['data_with_peaks_1'] = PeakDetectionTimeDomain(
    pipeline.time_average_normal_1,
    time_peak_windows=tw,
    peak_to_peak_measures=pm)
pipeline['data_with_peaks_2'] = PeakDetectionTimeDomain(
    pipeline.time_average_normal_2,
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

# %%
# Show some waveforms
# ------------------------------------


pipeline['plotter'] = PlotWaveforms(pipeline.data_with_peaks_1,
                                    ch_to_plot=np.array(['C4', 'CP2', 'GFP']),
                                    overlay=[pipeline.data_with_peaks_2],
                                    statistical_test='f_test_time',
                                    show_following_stats=['f', 'rn'],
                                    return_figures=True,
                                    )
pipeline.run()

# %%
# Show some topographic maps
# ------------------------------------


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline.data_with_peaks_1,
                                                   topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   user_naming_rule='standard',
                                                   return_figures=True)
pipeline['topographic_map_2'] = PlotTopographicMap(pipeline.data_with_peaks_2,
                                                   topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   user_naming_rule='dss',
                                                   return_figures=True)
pipeline.run()

# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}
database_path = reader.input_node.paths.test_path.joinpath('acc_test_data_filters.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline.data_with_peaks_1,
                                                      pipeline.data_with_peaks_2,
                                                      pipeline.ht2_1,
                                                      pipeline.ht2_2]
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
