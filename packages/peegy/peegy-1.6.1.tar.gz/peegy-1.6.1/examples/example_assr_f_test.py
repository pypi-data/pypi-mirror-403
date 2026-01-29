"""
.. _tut-assr-f-test-sim:

##############################################
ASSR F-Test Example (Simulated)
##############################################

In this example we simulate an ASSR and we investigate the significance of the response by means of an F test that
compares the variance of the frequency of interest with the variance of neighbouring frequency bins

"""
# Enable below for interactive backend
# import matplotlib
# if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
#     matplotlib.use('Qt5Agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels, ReSampling
from peegy.processing.pipe.epochs import AverageEpochs, EpochData
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.statistics import FTest
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
from peegy.processing.pipe.time_frequency import TimeFrequencyResponse, PlotTimeFrequencyData
import os
import astropy.units as u
import numpy as np
from peegy.io.storage.data_storage_reading_tools import sqlite_tables_to_pandas
from peegy.io.storage.plot_tools import plot_topographic_maps

# %%
# Generate some data
# =================================
# We generate some auditory steady-state response (ASSR)


fs = 400.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 6 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
test_frequencies = np.array([assr_frequency.value]) * u.Hz
# here we pick some random frequencies to test statistical detection
random_frequencies = np.round(np.unique(np.random.rand(1) * 5), decimals=1) * u.Hz
template_waveform, _ = aep(fs=fs)
n_channels = 32
event_times = np.arange(0, 360.0, 1 / assr_frequency.to(u.Hz).value) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels)) / n_channels,
                           snr=5,
                           layout_file_name='biosemi32.lay',
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='assr_f_test',
                           events_asymmetry_factor=0.7,
                           events_asymmetry_interval=2)
reader.run()

# %%
# Resize events
# ============================
# Now we keep events at intervals that correspond to our desired epoch length


events = reader.output_node.events.get_events(code=1)
# skip events to preserve only those at each epoch point
_new_events = Events(events=events[0:-1:int(epoch_length * assr_frequency)])
reader.output_node.events = _new_events

# %%
# Start the pipeline
# =============================
# Some processing to obtain clean epochs


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader, reference_channels=['Cz'], invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['down_sampled'] = ReSampling(pipeline['channel_cleaned'], new_sampling_rate=200 * u.Hz)
pipeline['time_filtered_data'] = FilterData(pipeline['down_sampled'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=90.0 * u.Hz)
pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False)
pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(
    pipeline['time_epochs'],
    components_to_plot=np.arange(0, 5),
    projection_domain=Domain.frequency,
    test_frequencies=test_frequencies,
    return_figures=True)
pipeline.run()

# %%
# Append GFP channel
# ---------------------------------------
# Now we keep events at intervals that correspond to our desired epoch length

pipeline['time_ave_dss'] = AverageEpochs(pipeline['dss_time_epochs'])
pipeline['time_ave'] = AverageEpochs(pipeline['time_epochs'])
pipeline.run()
##
pipeline['time_ave_dss_with_gfp'] = AppendGFPChannel(pipeline['time_ave_dss'])
pipeline['time_ave_with_gfp'] = AppendGFPChannel(pipeline['time_ave'])

pipeline.run()

# plot time frequency response
pipeline['time_freq_transformation'] = TimeFrequencyResponse(pipeline['time_ave_dss_with_gfp'])
pipeline['plot_time_freq'] = PlotTimeFrequencyData(pipeline['time_freq_transformation'],
                                                   plot_x_lim=[0, 1],
                                                   topographic_channels=np.array(['P8']),
                                                   db_scale=False)
pipeline.run()
# %%
# Run F-Test
# ---------------------------------------
# Now we run an F-test to determine if frequency component is significant

pipeline['fft_ave_f_tests_dss'] = FTest(pipeline['time_ave_dss_with_gfp'],
                                        n_fft=int(epoch_length * fs * 1),
                                        test_frequencies=np.append(random_frequencies,
                                                                   [assr_frequency, 2 * assr_frequency]),
                                        delta_frequency=15.0 * u.Hz)

pipeline['fft_ave_f_tests'] = FTest(pipeline['time_ave_with_gfp'],
                                    n_fft=int(epoch_length * fs * 1),
                                    test_frequencies=np.append(random_frequencies,
                                                               [assr_frequency, 2 * assr_frequency]),
                                    delta_frequency=9.0 * u.Hz)
pipeline.run()
pipeline['fft_ave_f_tests_dss'].output_node.statistical_tests['f_test_freq'][
    ["test_name", "df_1", "df_2", "f", "f_critic", "p_value"]].head()

# %%
# Generate figures
# ---------------------------------------
# Now plot the results


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['fft_ave_f_tests_dss'],
                                                   topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 3],
                                                   return_figures=True,
                                                   user_naming_rule='dss')
pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['fft_ave_f_tests'],
                                                   topographic_channels=np.array(['C4', 'CP2', 'GFP']),
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 3],
                                                   return_figures=True,
                                                   user_naming_rule='standard')
pipeline['plotter'] = PlotWaveforms(pipeline['fft_ave_f_tests'],
                                    ch_to_plot=np.array(['C4', 'CP2', 'GFP']),
                                    overlay=[pipeline['fft_ave_f_tests_dss']],
                                    plot_x_lim=[0, 90],
                                    plot_y_lim=[-1, 1.5],
                                    offset_step=0.3 * u.uV,
                                    statistical_test='f_test_freq',
                                    show_following_stats=['frequency_tested', 'f'],
                                    user_naming_rule='waveforms',
                                    return_figures=True,
                                    fig_format='.png')
pipeline.run()

# %%
# Save results to a database
# ---------------------------------------
# We get the measurements we are interested in and save them into a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')
_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.test_path.joinpath('assr_f_test_data.sqlite')
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

# %%
# Read frequency amplitude from generated database and plot the topographic map
# ------------------------------------_______________________________________________
df = sqlite_tables_to_pandas(database_path=database_path,
                             tables=['peaks_frequency'])

fig_out = plot_topographic_maps(dataframe=df.peaks_frequency,
                                channels_column='channel',
                                cols_by='x',
                                topographic_value='amp',
                                layout='biosemi32.lay',
                                title_by='col',
                                title_v_offset=-0.05,
                                color_map_label='Amplitude [$\mu$V]'
                                )
