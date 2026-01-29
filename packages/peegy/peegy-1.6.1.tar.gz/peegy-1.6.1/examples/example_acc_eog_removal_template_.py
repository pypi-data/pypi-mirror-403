"""
.. _tut-acc-eog-removal-sim:

##################################
EOG removal (Simulated)
##################################

This example illustrates removal of the eye artefacts via a template subtraction method
described in Valderrama et al, 2018. This script will output a figure, showing the
estimated eye artefact, and the EEG signal before and after eye artefact removal.
The algorithm performs three steps:
1) Blinks are detected in each channel using a (generic) eye artefact template.
The template is iteratively adjusted after each newly detected eye blink, to more closely match
the individual subject one.
2) A signal is generated, which used the individual template to represent all detected eyeblinks,
depending on the amplitudes and timepoints of each individual eyeblink.
3) The signal from step two is subtracted from the raw EEG signal, thus leading to an enhanced
EEG signal, where eyeblinks do not lead to dropping of the affected epochs.
Literature:
Valderrama, J. T., de la Torre, A., & Van Dun, B. (2018). An automatic algorithm for blink-artifact suppression based
on iterative template matching: Application to single channel recording of cortical auditory evoked potentials.
Journal of Neural Engineering, 15(1), 016008. https://doi.org/10.1088/1741-2552/aa8d95

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.pipe.detection import PeakDetectionTimeDomain
from peegy.processing.pipe.general import ReferenceData, FilterData, RegressOutEOG, ReSampling, AutoRemoveBadChannels, \
    BaselineCorrection
from peegy.processing.pipe.epochs import AverageEpochs, EpochData
from peegy.processing.pipe.attach import AppendGFPChannel
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
# Time windows
# ======================
# Time windows are used to define where to look for different peaks


tw = np.array([TimePeakWindow(ini_time=50 * u.ms, end_ref='N1', label='P1', positive_peak=True,
                              exclude_channels=['GFP']),
               TimePeakWindow(ini_time=100 * u.ms, end_time=200 * u.ms, label='N1', positive_peak=False,
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


roi_windows = np.array([TimeROI(ini_time=100.0 * u.ms, end_time=250.0 * u.ms, label="acc")])

# %%
# Generate some data
# =============================
# First we generate some ACC data

n_channels = 32
fs = 512.0 * u.Hz
template_waveform, _ = aep(fs=fs)
event_times = np.arange(0, 100.0, 1.0)
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           layout_file_name='biosemi32.lay',
                           snr=0.1,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='acc_test_eog_template',
                           include_eog_events=True,
                           include_non_stationary_noise_events=True,
                           noise_seed=0
                           )
reader.run()

# %%
# Start the pipeline
# =============================
# Now we proceed with our basic processing pipeline


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader, reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['down_sampled'] = ReSampling(pipeline['channel_cleaned'],
                                      new_sampling_rate=256. * u.Hz)
pipeline.run()
pipeline['eog_removed'] = RegressOutEOG(pipeline['down_sampled'],
                                        ref_channel_labels=['EOG1'],
                                        method='template',
                                        n_iterations=10,
                                        use_initial_template=True)
pipeline.run()

# %%
# Show EOG removal Output
# ------------------------------------


pipeline['eog_removed'].plot(plot_input=True,
                             plot_output=True,
                             ch_to_plot=['CP1', 'CP5', 'P7'],
                             interactive=False)

# %%
# Continue with the pipeline
# ------------------------------------


pipeline['time_filtered_data_eog_removed'] = FilterData(pipeline['eog_removed'],
                                                        high_pass=2.0 * u.Hz,
                                                        low_pass=30.0 * u.Hz)
pipeline['time_filtered_data_with_eog_artefacts'] = FilterData(pipeline['down_sampled'],
                                                               high_pass=2.0 * u.Hz,
                                                               low_pass=30.0 * u.Hz)
pipeline.run()

# %%
# Get Epochs
# ------------------------------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs_eog_removed'] = EpochData(pipeline['time_filtered_data_eog_removed'],
                                                event_code=1.0)
pipeline['time_epochs_with_eog_artefacts'] = EpochData(pipeline['time_filtered_data_with_eog_artefacts'],
                                                       event_code=1.0)
pipeline.run()
# %%
# Get DSS components for EOG free
# ------------------------------------
# Compute spatial filter based on EOG free epochs


pipeline['time_epochs_with_eog_removed_dss'] = CreateAndApplySpatialFilter(pipeline['time_epochs_eog_removed'],
                                                                           sf_components=np.arange(5),
                                                                           user_naming_rule='dss_no_artefacts',
                                                                           return_figures=True)
pipeline.run()

# %%
# Get DSS components for contaminated data
# -----------------------------------------
# Compute spatial filter based on EOG contaminated epochs


pipeline['time_epochs_with_eog_artefacts_and_dss'] = CreateAndApplySpatialFilter(
    pipeline['time_epochs_with_eog_artefacts'],
    sf_components=np.arange(5),
    return_figures=True,
    user_naming_rule='dss_eog_artefacts')
pipeline.run()

# %%
# Compute global field power (GFP)
# ------------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data


pipeline['time_epochs_eog_removed_gfp'] = AppendGFPChannel(pipeline['time_epochs_eog_removed'])
pipeline['time_epochs_with_eog_artefacts_gfp'] = AppendGFPChannel(pipeline['time_epochs_with_eog_artefacts'])
pipeline['time_epochs_with_eog_artefacts_and_dss_gfp'] = AppendGFPChannel(
    pipeline['time_epochs_with_eog_artefacts_and_dss'])
pipeline['time_epochs_with_eog_removed_dss_gfp'] = AppendGFPChannel(pipeline['time_epochs_with_eog_removed_dss'])

pipeline.run()

# %%
# Base line correction
# ------------------------------------
# We correct the initial segment by removing the mean in the first 20 ms


pipeline['time_epochs_eog_removed_gfp_baseline_corrected'] = BaselineCorrection(
    pipeline['time_epochs_eog_removed_gfp'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)

pipeline['time_epochs_with_eog_artefacts_gfp_baseline_corrected'] = BaselineCorrection(
    pipeline['time_epochs_with_eog_artefacts'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)

pipeline['time_epochs_with_eog_artefacts_and_dss_gfp_baseline_corrected'] = BaselineCorrection(
    pipeline['time_epochs_with_eog_artefacts_and_dss_gfp'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)

pipeline['time_epochs_with_eog_removed_dss_gfp_baseline_corrected'] = BaselineCorrection(
    pipeline['time_epochs_with_eog_removed_dss_gfp'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)
pipeline.run()

# %%
# Compute HT2 statistics
# ------------------------------------
# Using the raw epochs we estimate Hotelling-T2 statistics


pipeline['ht2'] = HotellingT2Test(pipeline['time_epochs_eog_removed_gfp_baseline_corrected'],
                                  roi_windows=roi_windows)
pipeline['ht2_eog_artefacts'] = HotellingT2Test(pipeline['time_epochs_with_eog_artefacts_gfp_baseline_corrected'],
                                                roi_windows=roi_windows)
pipeline.run()
pipeline['ht2'].output_node.statistical_tests['hotelling_t2_time'][[
    "test_name", "df_1", "df_2", "f", "f_critic", "p_value"]].head()

# %%
# Compute average responses
# ------------------------------------
# We apply different types of averages and compute the mean


pipeline['time_average_eog_removed'] = AverageEpochs(
    pipeline['time_epochs_eog_removed_gfp_baseline_corrected'],
    roi_windows=roi_windows,
    weighted_average=False)

pipeline['time_average_with_eog_artefacts'] = AverageEpochs(
    pipeline['time_epochs_with_eog_artefacts_gfp_baseline_corrected'],
    roi_windows=roi_windows,
    weighted_average=False)

pipeline['time_w_average_with_eog_artefacts'] = AverageEpochs(
    pipeline['time_epochs_with_eog_artefacts_gfp_baseline_corrected'],
    roi_windows=roi_windows,
    weighted_average=True)

pipeline['time_average_with_eog_artefacts_dss'] = AverageEpochs(
    pipeline['time_epochs_with_eog_artefacts_and_dss_gfp_baseline_corrected'],
    roi_windows=roi_windows,
    weighted_average=True)

pipeline['time_average_with_eog_removed_dss'] = AverageEpochs(
    pipeline['time_epochs_with_eog_removed_dss_gfp_baseline_corrected'],
    roi_windows=roi_windows,
    weighted_average=True)
pipeline.run()

# %%
# Show an average response
# ------------------------------------
# The red traces show the input epochs whist the blue traces shows the average response


pipeline['time_average_eog_removed'].plot(plot_input=False,
                                          plot_output=True,
                                          ch_to_plot=['CP1', 'CP5', 'P7'],
                                          interactive=False)

# %%
# Detect peaks
# ------------------------------------
# Using the average data, we proceed detecting peaks


pipeline['data_with_peaks_eog_removed'] = PeakDetectionTimeDomain(pipeline['time_average_eog_removed'],
                                                                  time_peak_windows=tw,
                                                                  peak_to_peak_measures=pm)
pipeline['data_with_peaks_with_eog_artefacts'] = PeakDetectionTimeDomain(pipeline['time_average_with_eog_artefacts'],
                                                                         time_peak_windows=tw,
                                                                         peak_to_peak_measures=pm)

pipeline['data_with_peaks_with_eog_artefacts_weighted_average'] = PeakDetectionTimeDomain(
    pipeline['time_w_average_with_eog_artefacts'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

pipeline['data_with_peaks_with_eog_removed_dss'] = PeakDetectionTimeDomain(
    pipeline['time_average_with_eog_removed_dss'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

pipeline['data_with_peaks_with_eog_artefacts_and_dss'] = PeakDetectionTimeDomain(
    pipeline['time_average_with_eog_artefacts_dss'],
    time_peak_windows=tw,
    peak_to_peak_measures=pm)

pipeline.run()

# %%
# Show topographic maps
# ------------------------------------


pipeline['plotter_1'] = PlotTopographicMap(pipeline['data_with_peaks_eog_removed'],
                                           topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                           plot_x_lim=[0, 0.8],
                                           plot_y_lim=[-3, 3],
                                           user_naming_rule='eog_free')

pipeline['plotter_2'] = PlotTopographicMap(pipeline['data_with_peaks_with_eog_artefacts'],
                                           topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                           plot_x_lim=[0, 0.8],
                                           plot_y_lim=[-3, 3],
                                           user_naming_rule='with_eog')
pipeline['plotter_3'] = PlotTopographicMap(pipeline['data_with_peaks_with_eog_artefacts_weighted_average'],
                                           topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                           plot_x_lim=[0, 0.8],
                                           plot_y_lim=[-3, 3],
                                           user_naming_rule='with_eog_weighted_average')

pipeline['plotter_4'] = PlotTopographicMap(pipeline['data_with_peaks_with_eog_removed_dss'],
                                           topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                           plot_x_lim=[0, 0.8],
                                           plot_y_lim=[-3, 3],
                                           user_naming_rule='with_eog_removed_dss')

pipeline['plotter_5'] = PlotTopographicMap(pipeline['data_with_peaks_with_eog_artefacts_and_dss'],
                                           topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                           plot_x_lim=[0, 0.8],
                                           plot_y_lim=[-3, 3],
                                           user_naming_rule='with_eog_artefacts_and_dss')

pipeline['plotter_5'] = PlotWaveforms(pipeline['data_with_peaks_eog_removed'],
                                      overlay=[
                                          pipeline['data_with_peaks_with_eog_artefacts_and_dss'],
                                          pipeline['data_with_peaks_with_eog_artefacts_weighted_average'],
                                          pipeline['data_with_peaks_with_eog_removed_dss']],
                                      ch_to_plot=np.array(['C4', 'CP2', 'GFP']),
                                      return_figures=True)

pipeline.run()

# %%
# Get generated data and save to database
# ------------------------------------------------
# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}
database_path = reader.input_node.paths.test_path.joinpath('acc_test_data_eog_template.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['data_with_peaks_eog_removed'],
                                                      pipeline['data_with_peaks_with_eog_artefacts_and_dss'],
                                                      pipeline['data_with_peaks_with_eog_artefacts_weighted_average'],
                                                      pipeline['ht2'],
                                                      pipeline['ht2_eog_artefacts'],
                                                      pipeline['time_epochs_with_eog_removed_dss']]
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=1200)
