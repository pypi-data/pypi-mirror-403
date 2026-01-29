"""
.. _tut-acc-bootstrapping-pipeline-sim:

########################################################
ACC Standard analysis (Simulated) using bootstrap
########################################################

In this example we simulate an ACC response and detect the peaks using standard and bootstrapping methods.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.detection.definitions import TimePeakWindow, PeakToPeakMeasure, TimeROI
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.bootstrap.bootstrap import Bootstrap, BootstrapTarget
from peegy.processing.pipe.general import FilterData, ReSampling, AutoRemoveBadChannels, ReferenceData, RegressOutEOG, \
    BaselineCorrection
from peegy.processing.pipe.epochs import EpochData, AverageEpochs, ApplyFunctionToTimeROI
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
    [TimeROI(ini_time=100.0 * u.ms, end_time=600.0 * u.ms, label="acc_snr"),
     TimeROI(ini_time=2100.0 * u.ms, end_time=2600.0 * u.ms, label="control")])

# %%
# Generate some data
# ===================
# First we generate some ACC data

n_channels = 32
fs = 512.0 * u.Hz
template_waveform, _ = aep(fs=fs, time_length=0.6 * u.s)
event_times = np.arange(0, 400.0, 4.0) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           layout_file_name='biosemi32.lay',
                           snr=0.1,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='acc_test',
                           include_eog_events=True,
                           noise_attenuation=3
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

pipeline['time_filtered_data'] = FilterData(pipeline.eog_removed,
                                            high_pass=2.0 * u.Hz,
                                            low_pass=30.0 * u.Hz)

pipeline.run()

# %%
# Bootstrapping
# ------------------------------------
# We generate a new pipeline indicating what would be bootstrapped
pipeline_bootstrap = PipePool()

pipeline_bootstrap['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                              event_code=1.0,
                                              pre_stimulus_interval=200 * u.ms,
                                              post_stimulus_interval=4 * u.s)
pipeline_bootstrap['time_epochs_dss'] = CreateAndApplySpatialFilter(input_process=pipeline_bootstrap['time_epochs'],
                                                                    plot_projections=False,
                                                                    components_to_plot=None,
                                                                    plot_power=False)
pipeline_bootstrap['time_epochs_with_baseline_corrected'] = BaselineCorrection(
    pipeline_bootstrap['time_epochs_dss'],
    ini_time=0 * u.ms,
    end_time=20 * u.ms)
pipeline_bootstrap['ht2'] = HotellingT2Test(pipeline_bootstrap['time_epochs_with_baseline_corrected'],
                                            roi_windows=roi_windows)
pipeline_bootstrap['ftest'] = AverageEpochs(pipeline_bootstrap['time_epochs_with_baseline_corrected'],
                                            roi_windows=roi_windows,
                                            weighted_average=False)

pipeline_bootstrap['roi_rms'] = ApplyFunctionToTimeROI(
    pipeline_bootstrap['ftest'],
    roi_windows=roi_windows,
    test_name='rms',
    function_object=lambda x: np.sqrt(np.mean(x ** 2, axis=0)))

pipeline_bootstrap['roi_variance'] = ApplyFunctionToTimeROI(
    pipeline_bootstrap['ftest'],
    roi_windows=roi_windows,
    test_name='variance',
    function_object=lambda x: np.std(x ** 2, axis=0, ddof=1) ** 2.0)

pipeline_bootstrap['roi_area'] = ApplyFunctionToTimeROI(
    pipeline_bootstrap['ftest'],
    roi_windows=roi_windows,
    test_name='area',
    function_object=lambda x: np.sum(np.abs(x) * 1 / pipeline['time_filtered_data'].output_node.fs, axis=0))
# bootstrap the pipe
pipeline['bootstrap'] = Bootstrap(at_each_bootstrap_do=pipeline_bootstrap,
                                  n_bootstraps=100,
                                  event_code=1.0,
                                  n_jobs=1,
                                  bootstrap_targets=[
                                      BootstrapTarget(
                                          test_name='HT2',
                                          group_by=['channel', 'label', 'ini_time', 'end_time'],
                                          target_values=['f']),
                                      BootstrapTarget(
                                          test_name='Fmp',
                                          group_by=['channel', 'label', 'ini_time', 'end_time'],
                                          target_values=['f']),
                                      BootstrapTarget(
                                          test_name='rms',
                                          group_by=['channel', 'label', 'ini_time', 'end_time'],
                                          target_values=['function_value']),
                                      BootstrapTarget(
                                          test_name='variance',
                                          group_by=['channel', 'label', 'ini_time', 'end_time'],
                                          target_values=['function_value']),
                                      BootstrapTarget(
                                          test_name='area',
                                          group_by=['channel', 'label', 'ini_time', 'end_time'],
                                          target_values=['function_value'])
                                  ]
)
pipeline.run()

# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}
database_path = reader.input_node.paths.test_path.joinpath('acc_test_bootstrap_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['bootstrap']]
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
