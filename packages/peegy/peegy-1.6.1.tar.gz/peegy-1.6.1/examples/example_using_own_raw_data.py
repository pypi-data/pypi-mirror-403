"""
.. _tut-assr-using-own-raw-data-sim:

#######################################################################
ASSR F-Test Example using 'external' data (time x channels) (Simulated)
#######################################################################

This example shows how you can pass any data to the pipeline (e.g. matlab data, or text file data) in the shape of time
x channels alongside with event times used to epoch the data.
In this example we simulate an ASSR (as it was read from an external file), and we investigate the significance of
the response by means of an F-test that compares the variance of the frequency of interest with the variance of
neighbouring frequency bins.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Domain
from peegy.processing.pipe.io import GenericInputData
from peegy.processing.pipe.statistics import FTest
from peegy.processing.pipe.general import FilterData
from peegy.processing.pipe.epochs import AverageEpochs, EpochData
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import peegy.definitions.default_paths as default_paths
import os
import astropy.units as u
import numpy as np

# %%
# Generate some data (time x channels) and add event times
# ==========================================================
# We generate some data in this example, for the sake of exemplify it. The data is put into GenericInputData class and
# then used in a standard pipeline


fs = 256.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 41.0 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
test_frequencies = np.array([assr_frequency.value, 2 * assr_frequency.value]) * u.Hz
# here we generate and pass our own data
n_epochs = 20
time = np.arange(0, epoch_length.to(u.s).value * n_epochs, 1 / fs.to(u.Hz).value) * u.s
my_sin = np.sin(2 * np.pi * u.rad * assr_frequency * time)
template_waveform = np.array([my_sin, 0.5 * my_sin, 0.25 * my_sin]).T
# add some noise
np.random.seed(1)
template_waveform = template_waveform + np.random.randn(*template_waveform.shape)
event_times = np.arange(0, n_epochs) * epoch_length
reader = GenericInputData(data=template_waveform,
                          fs=fs,
                          event_times=event_times,
                          event_code=1.0,
                          figures_folder=default_paths.test_figures_path,
                          figures_subset_folder='my_own_raw_assr_f_test')
reader.run()
# %%
# Start the pipeline
# ==========================================================


pipeline = PipePool()
pipeline['time_filtered_data'] = FilterData(reader,
                                            high_pass=2.0 * u.Hz,
                                            low_pass=100.0 * u.Hz)
pipeline.run()

# %%
# Get Epochs
# -----------------------------------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False)
pipeline.run()

# %%
# Get DSS components and clean data
# -----------------------------------------
# Compute spatial filter of time epochs


pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          test_frequencies=test_frequencies,
                                                          components_to_plot=np.arange(0, 5),
                                                          projection_domain=Domain.frequency)
pipeline.run()

# %%
# Compute average responses
# -----------------------------------------
# We compute weighted average on epochs with and without spatial filtering (DSS)

pipeline['time_ave_dss'] = AverageEpochs(pipeline['dss_time_epochs'])
pipeline['time_ave'] = AverageEpochs(pipeline['time_epochs'])
pipeline.run()

# %%
# Run F-Test
# -----------------------------------------
# Now we run an F-test to determine if frequency component is significant


pipeline['fft_ave_f_tests_dss'] = FTest(pipeline['time_ave_dss'],
                                        n_fft=int(epoch_length*fs*1),
                                        test_frequencies=test_frequencies,
                                        delta_frequency=9.0 * u.Hz)
pipeline['fft_ave_f_tests'] = FTest(pipeline['time_ave'],
                                    n_fft=int(epoch_length * fs * 1),
                                    test_frequencies=test_frequencies,
                                    delta_frequency=9. * u.Hz)

# %%
# Show some waveforms
# -----------------------------------------

pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['fft_ave_f_tests_dss'],
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 4],
                                                   topographic_channels=np.array(['CH_0', 'CH_1', 'CH_2']),
                                                   return_figures=True,
                                                   user_naming_rule='dss')

pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['fft_ave_f_tests'],
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 4],
                                                   topographic_channels=np.array(['CH_0', 'CH_1', 'CH_2']),
                                                   return_figures=True,
                                                   user_naming_rule='standard')

pipeline['plotter'] = PlotWaveforms(pipeline['fft_ave_f_tests'],
                                    ch_to_plot=np.array(['CH_0']),
                                    overlay=[pipeline['fft_ave_f_tests_dss']],
                                    plot_x_lim=[0, 90],
                                    show_following_stats=['frequency_tested', 'f'],
                                    return_figures=True,
                                    user_naming_rule='waveforms',
                                    fig_format='.png')
pipeline.run()

# %%
# Get generated data and save to database
# -----------------------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')
_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.test_path.joinpath('assr_own_raw_data_f_test_data.sqlite')
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
# -----------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
