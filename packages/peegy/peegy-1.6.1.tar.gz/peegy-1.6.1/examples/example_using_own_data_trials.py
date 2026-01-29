"""
.. _tut-assr-using-own-data-trials-test-sim:

#################################################################################
ASSR F-Test Example using 'external' data (time x channels x trials) (Simulated)
#################################################################################

This example illustrates how you can use any generic data (e.g. matlab data, or text file data) in the shape of time x
channels x trials.
In this example we simulate an ASSR, and we investigate the significance of the response by means of an F-test that
compares the variance of the frequency of interest with the variance of neighbouring frequency bins

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Domain
from peegy.processing.pipe.io import GenericInputData
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.statistics import FTest
from peegy.processing.pipe.general import FilterData
from peegy.processing.pipe.epochs import AverageEpochs
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
from peegy.processing.pipe.attach import CombineChannels
import peegy.definitions.default_paths as default_paths
import os
import astropy.units as u
import numpy as np

# %%
# Generate some data (time x channels x trials)
# =============================================
# We generate some data in the shape of time x channels x trials and put it into a GenericInputData class

fs = 256.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = np.array([41.0]) * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
# here we generate and pass our own data
n_epochs = 20
time = np.arange(0, epoch_length.to(u.s).value, 1 / fs.to(u.Hz).value) * u.s
my_sin = np.sin(2 * np.pi * u.rad * assr_frequency * time)
template_waveform = np.array([my_sin, 0.5 * my_sin, 0.25 * my_sin]).T
template_waveform = np.repeat(template_waveform[:, :, None], n_epochs, axis=2)
# add some noise
np.random.seed(1)
template_waveform = template_waveform + np.random.randn(*template_waveform.shape)

reader = GenericInputData(data=template_waveform,
                          fs=fs,
                          figures_folder=default_paths.test_figures_path,
                          figures_subset_folder='my_own_trials_assr_f_test')
reader.run()

# %%
# Start the pipeline
# ============================
pipeline = PipePool()
pipeline['time_filtered_data'] = FilterData(reader,
                                            high_pass=2.0 * u.Hz,
                                            low_pass=100.0 * u.Hz)
pipeline.run()

# %%
# Get DSS components for cleaned data
# ------------------------------------
# Compute spatial filter based on artefact free epochs

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_filtered_data'],
                                                          test_frequencies=np.concatenate((assr_frequency,
                                                                                           2 * assr_frequency)),
                                                          components_to_plot=np.arange(0, 5),
                                                          projection_domain=Domain.frequency)
pipeline.run()


pipeline['combined'] = CombineChannels(pipeline['time_filtered_data'],
                                       channel_labels=['CH_0', 'CH_1'],
                                       function=lambda x: np.mean(x, axis=1, keepdims=True)
                                       )

# %%
# Compute global field power (GFP)
# ------------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data

pipeline['dss_time_epochs_with_gfp'] = AppendGFPChannel(pipeline['dss_time_epochs'])
pipeline['time_epochs_with_gfp'] = AppendGFPChannel(pipeline['combined'])
pipeline.run()

# %%
# Compute average responses
# ------------------------------------
# Apply averages to data

pipeline['time_ave_dss'] = AverageEpochs(pipeline['dss_time_epochs_with_gfp'])
pipeline['time_ave'] = AverageEpochs(pipeline['time_epochs_with_gfp'])
pipeline.run()

# %%
# Run F-Test
# ------------------------------------
# Now we run an F-test to determine if frequency component is significant

pipeline['fft_ave_f_tests_dss'] = FTest(pipeline['time_ave_dss'],
                                        n_fft=int(epoch_length*fs*1),
                                        test_frequencies=assr_frequency,
                                        delta_frequency=9.0 * u.Hz)
pipeline['fft_ave_f_tests'] = FTest(pipeline['time_ave'],
                                    n_fft=int(epoch_length * fs * 1),
                                    test_frequencies=assr_frequency,
                                    delta_frequency=9.0 * u.Hz)
pipeline.run()

# %%
# Generate figures
# ------------------------------------
# Now plot the results


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['fft_ave_f_tests_dss'],
                                                   topographic_channels=np.array(['CH_0', 'CH_1', 'CH_2']),
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 4],
                                                   return_figures=True,
                                                   user_naming_rule='dss')
pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['fft_ave_f_tests'],
                                                   topographic_channels=np.array(['CH_0', 'CH_1', 'CH_2']),
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 4],
                                                   return_figures=True,
                                                   user_naming_rule='standard')
pipeline['plotter'] = PlotWaveforms(pipeline['fft_ave_f_tests'],
                                    ch_to_plot=np.array(['CH_0', 'CH_1', 'CH_2', 'CH_0_CH_1']),
                                    overlay=[pipeline['fft_ave_f_tests_dss']],
                                    plot_x_lim=[0, 90],
                                    statistical_test='f_test_freq',
                                    show_following_stats=['frequency_tested', 'f'],
                                    user_naming_rule='waveforms',
                                    return_figures=True,
                                    fig_format='.png')

pipeline.run()

# %%
# Get generated data and save to database
# ------------------------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')
_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.test_path.joinpath('assr_own_trials_data_f_test_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave_f_tests'],
                                                      pipeline['fft_ave_f_tests_dss']],
                                      include_waveforms=True
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
