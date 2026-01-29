"""
.. _tut-assr-phase-locking-sim:

########################################################
ASSR Phase Locking Value Test Example (Simulated)
########################################################

In this example we simulate an ASSR, and we investigate the significance of the phase by means of a Rayleigh Test on
the frequency of interest

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels
from peegy.processing.pipe.epochs import EpochData
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.statistics import PhaseLockingValue
from peegy.processing.pipe.plot import PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import astropy.units as u
import numpy as np


# %%
# Generate some data
# ===================
# We generate some auditory steady-state response (ASSR)


fs = 256.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 41.0 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
# here we pick some random frequencies to test statistical detection
random_frequencies = np.unique(np.random.rand(10) * 5) * u.Hz
template_waveform, _ = aep(fs=fs)
n_channels = 32
event_times = np.arange(0, 360.0, 1 / assr_frequency.to(u.Hz).value) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           snr=0.01,
                           layout_file_name='biosemi32.lay',
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='assr_plv_rayleigh_test')
reader.run()

# %%
# Resize events
# ========================
# Now we keep events at intervals that correspond to our desired epoch length
events = reader.output_node.events.get_events(code=1)
# skip events to preserve only those at each epoch point
_new_events = Events(events=events[0:-1:int(epoch_length * assr_frequency)])
reader.output_node.events = _new_events

# %%
# Start the pipeline
# ========================
# Some processing to obtain clean epochs


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader, reference_channels=['Cz'], invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['time_filtered_data'] = FilterData(pipeline['channel_cleaned'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=100.0 * u.Hz)
pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False)
pipeline.run()

# %%
# Compute and plot components in the frequency-domain
# -----------------------------------------------------
# Spatial filter is a applied in the frequency-domain

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          test_frequencies=np.array([assr_frequency.to(u.Hz).value]),
                                                          sf_components=np.arange(0, 2),
                                                          components_to_plot=np.arange(0, 5),
                                                          projection_domain=Domain.frequency)
pipeline.run()

# %%
# Compute global field power (GFP)
# ---------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data


pipeline['dss_time_epochs_with_gfp'] = AppendGFPChannel(pipeline['dss_time_epochs'])
pipeline.run()

# %%
# Run Rayleigh Tests (phase-locking value)
# -----------------------------------------
# Now we run an Rayleigh Tests to determine if frequency component is significantly phase-locked


pipeline['rayleigh_tests'] = PhaseLockingValue(pipeline['dss_time_epochs_with_gfp'],
                                               n_fft=int(epoch_length*fs*1),
                                               test_frequencies=np.append(random_frequencies,
                                                                          [assr_frequency, 2 * assr_frequency]),
                                               weight_data=True)

# %%
# Generate Phase-locking figures
# ---------------------------------
# Now we plot PLV in the frequency-domain


pipeline['topographic_map_1'] = PlotTopographicMap(pipeline['rayleigh_tests'],
                                                   topographic_channels=np.array(['O2', 'T8', 'T7', 'GFP']),
                                                   plot_x_lim=[0, 90],
                                                   plot_y_lim=[0, 1.2],
                                                   return_figures=True)
pipeline.run()

# %%
# Save results to a database
# ---------------------------------
# We get the measurements we are interested in and save them into a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.test_path.joinpath('assr_rayleigh_test_data.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['rayleigh_tests']],
                                      include_waveforms=True
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
