"""
.. _tut-assr-no-layout-test-sim:

########################################################
ASSR Without using a topographic layout (Simulated)
########################################################

In this example we simulate an ASSR recorded without any specific layout.
The significance of the response is assessed using the Hotelling's T2 test.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels, RegressOutEOG, ReSampling
from peegy.processing.pipe.epochs import AverageEpochsFrequencyDomain, EpochData, AverageEpochs
from peegy.processing.pipe.plot import PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import astropy.units as u
import numpy as np
import peegy.definitions.default_paths as default_paths
# %%
# Generate some data
# ==================================
# We generate some auditory steady-state response (ASSR)


fs = 512.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 41.0 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
# here we pick some random frequencies to test statistical detection
random_frequencies = np.unique(np.random.rand(10)*30) * u.Hz
test_frequencies = np.concatenate(([assr_frequency], random_frequencies))
template_waveform, _ = aep(fs=fs)
n_channels = 8
event_times = np.arange(0, 360.0, 1/assr_frequency.to(u.Hz).value) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           snr=0.05,
                           include_eog_events=True,
                           event_times=event_times,
                           event_code=1.0,
                           figures_folder=default_paths.test_figures_path,
                           figures_subset_folder='assr_no_layout_test')
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
# ============================
# Some processing to obtain clean epochs


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['CH_0'],
                                       invert_polarity=False)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['eog_removed'] = RegressOutEOG(pipeline['channel_cleaned'],
                                        ref_channel_labels=['EOG1'])
pipeline['down_sampled'] = ReSampling(pipeline['eog_removed'],
                                      new_sampling_rate=256. * u.Hz)
pipeline['time_filtered_data'] = FilterData(pipeline['down_sampled'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=60.0 * u.Hz)
pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False,
                                    post_stimulus_interval=epoch_length)
pipeline.run()

# %%
# Compute and plot components in the frequency-domain
# ---------------------------------------------------
# Spatial filter is applied in the frequency-domain

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          projection_domain=Domain.frequency,
                                                          return_figures=True)
pipeline.run()

# %%
# Average epochs in time- and frequency-domain
# ----------------------------------------------
# We compute the average and simultaneously get statistical tests on the test_frequencies

pipeline['fft_ave'] = AverageEpochsFrequencyDomain(pipeline['dss_time_epochs'],
                                                   test_frequencies=test_frequencies)
pipeline['time_ave'] = AverageEpochs(pipeline['dss_time_epochs'])
pipeline.run()

# %%
# Generate figures
# ------------------
# Now we run plot the average waveforms


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['fft_ave'],
                                                   plot_x_lim=[0, 60],
                                                   plot_y_lim=[0, 6],
                                                   return_figures=True)
pipeline['topographic_map_2'] = PlotTopographicMap(pipeline['time_ave'],
                                                   times=np.array([0, 1 / assr_frequency.to(u.Hz).value]),
                                                   plot_x_lim=[0, epoch_length.to(u.s).value],
                                                   plot_y_lim=[-6, 6],
                                                   return_figures=True)
pipeline.run()

# %%
# Save results to a database
# ---------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ASSR'}

database_path = reader.input_node.paths.test_path.joinpath('assr_no_layout_test_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave']],
                                      include_waveforms=True
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
