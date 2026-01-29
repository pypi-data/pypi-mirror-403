"""
.. _tut-acc-standard-weighted-average-methods-pipeline-sim:

##################################################################
ACC Standard analysis with different average methods (Simulated)
##################################################################

In this example we simulate an ACC response and average it using standard average as well as two different weighted
average method.
The first method, estimates the weights by tracking the same time points across epochs. This means that a number of
epochs needs to be obtained to estimate the weights of those epochs.
The second method estimates the weights within each epoch. This means that each epoch has its own weight.
For cortical responses, the latter can be more beneficial as artefacts within an epoch will be outweighed for that epoch
only.

"""
# Enable below for interactive backend
# import matplotlib
# if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
#     matplotlib.use('Qt5Agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.general import FilterData, ReSampling, AutoRemoveBadChannels, ReferenceData, \
    BaselineCorrection
from peegy.processing.pipe.epochs import EpochData, AverageEpochs
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
                           figures_subset_folder='acc_test_weighted_average_types',
                           include_eog_events=True
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
# %%
# Continue with the pipeline
# ------------------------------------

pipeline['time_filtered_data'] = FilterData(pipeline['down_sampled'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=30.0 * u.Hz)

pipeline.run()

# %%
# Get Epochs
# ------------------------------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs'] = EpochData(pipeline.time_filtered_data,
                                    event_code=1.0)
pipeline.run()

# %%
# Compute global field power (GFP)
# ------------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data

pipeline['time_epochs_with_gfp'] = AppendGFPChannel(pipeline['time_epochs'])

# %%
# Base line correction
# ------------------------------------
# We correct the initial segment by removing the mean in the first 20 ms
pipeline['time_epochs_with_baseline_corrected'] = BaselineCorrection(
    pipeline['time_epochs_with_gfp'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)

pipeline.run()

# %%
# Compute HT2 statistics
# ------------------------------------
# Using the raw epochs we estimate Hotelling-T2 statistics

pipeline['ht2_standard'] = HotellingT2Test(pipeline.time_epochs_with_baseline_corrected,
                                           roi_windows=roi_windows,
                                           weight_data=False)

pipeline['ht2_across'] = HotellingT2Test(pipeline.time_epochs_with_baseline_corrected,
                                         roi_windows=roi_windows,
                                         weight_data=True,
                                         weight_across_epochs=True)
pipeline['ht2_within'] = HotellingT2Test(pipeline.time_epochs_with_baseline_corrected,
                                         roi_windows=roi_windows,
                                         weight_data=True,
                                         weight_across_epochs=False)

pipeline.run()

# %%
# Compute average responses
# ------------------------------------
# We compute weighted average on epochs with and without spatial filtering (DSS)

pipeline['time_average_standard'] = AverageEpochs(pipeline['time_epochs_with_baseline_corrected'],
                                                  roi_windows=roi_windows,
                                                  weighted_average=False)
pipeline['time_average_standard_gfp'] = AppendGFPChannel(pipeline['time_average_standard'],
                                                         channel_label='GFP2')


pipeline['time_average_across'] = AverageEpochs(pipeline['time_epochs_with_baseline_corrected'],
                                                roi_windows=roi_windows,
                                                weighted_average=True,
                                                weight_across_epochs=True)
pipeline['time_average_across_gfp'] = AppendGFPChannel(pipeline['time_average_across'],
                                                       channel_label='GFP2')

pipeline['time_average_within'] = AverageEpochs(pipeline['time_epochs_with_baseline_corrected'],
                                                roi_windows=roi_windows,
                                                weighted_average=True,
                                                weight_across_epochs=False)
pipeline['time_average_within_gfp'] = AppendGFPChannel(pipeline['time_average_within'],
                                                       channel_label='GFP2')

# %%
# Detect peaks
# ------------------------------------
# Using the average data, we proceed detecting peaks

pipeline['data_with_peaks_standard'] = PeakDetectionTimeDomain(
    pipeline['time_average_standard_gfp'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)


pipeline['data_with_peaks_across'] = PeakDetectionTimeDomain(
    pipeline['time_average_across_gfp'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

pipeline['data_with_peaks_within'] = PeakDetectionTimeDomain(
    pipeline['time_average_within_gfp'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

# %%
# Show some waveforms
# ------------------------------------


pipeline['plotter'] = PlotWaveforms(pipeline['data_with_peaks_standard'],
                                    ch_to_plot=np.array(['T7', 'C4', 'CP2', 'GFP']),
                                    overlay=[pipeline['data_with_peaks_across'], pipeline['data_with_peaks_within']],
                                    statistical_test='f_test_time',
                                    show_following_stats=['f', 'rn'],
                                    return_figures=True,
                                    )
pipeline.run()

# %%
# Show some topographic maps
# ------------------------------------

pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['data_with_peaks_standard'],
                                                   topographic_channels=np.array(['T7', 'C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   return_figures=True)


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['data_with_peaks_across'],
                                                   topographic_channels=np.array(['T7', 'C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   return_figures=True)
pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['data_with_peaks_within'],
                                                   topographic_channels=np.array(['T7',     'C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 0.8],
                                                   plot_y_lim=[-3, 3],
                                                   return_figures=True)
pipeline.run()

# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}
database_path = reader.input_node.paths.test_path.joinpath('acc_test_data_weighted_average_types.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['data_with_peaks_standard'],
                                                      pipeline['data_with_peaks_across'],
                                                      pipeline['data_with_peaks_within'],
                                                      pipeline['ht2_standard'],
                                                      pipeline['ht2_across'],
                                                      pipeline['ht2_within']]
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
