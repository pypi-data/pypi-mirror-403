import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.epochs_processing_tools import et_get_spatial_filtering, et_apply_spatial_filtering
from peegy.processing.tools.eeg_epoch_operators import et_unfold
from peegy.definitions.channel_definitions import Domain, ChannelItem
from peegy.processing.tools.epochs_processing_tools import et_ica_epochs
from peegy.processing.tools.eeg_epoch_operators import et_fold
from peegy.processing.pipe.epochs import AverageEpochs, AverageEpochsFrequencyDomain
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.definitions.tables import Tables
from peegy.processing.tools.filters.spatial_filtering.definitions import FilterType, DSSData
import numpy as np
import pandas as pd
import os
import copy
import astropy.units as u
from peegy.tools.units.unit_tools import set_default_unit
from PyQt5.QtCore import QLibraryInfo
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)


class SpatialFilter(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 sf_join_frequencies: type(np.array) | None = None,
                 demean_data: bool = True,
                 weight_data: bool = True,
                 weighted_frequency_domain: bool = False,
                 weight_across_epochs: bool = True,
                 keep0: int | None = None,
                 keep1: float = 1e-9,
                 perc0: float = .99,
                 perc1: float | None = None,
                 block_size: int = 10,
                 n_tracked_points: int | None = None,
                 delta_frequency: u.Quantity = 5 * u.Hz,
                 n_jobs: int = 1,
                 **kwargs):
        """
        This class will create a spatial filter based on the data. If sf_join_frequencies are passed, the spatial
        filter will use a biased function based on the covariance of those frequencies only.
        :param input_process:  InputOutputProcess Class
        :param sf_join_frequencies: numpy array indicating the biased frequencies (useful for steady-state responses)
        :param demean_data: if true, data will be demeaned prior filter estimation
        :param weight_data: if true, dss filter will be estimated using weights
        :param weighted_frequency_domain: boll indicating if the weghts are compute in the time or frequency domain
        :param weight_across_epochs: if True, weights are computed across epochs (as in Elbeling 1984) otherwise weights
        are computed within epoch (1 / variance across time)
        :param keep0: integer controlling  whitening of unbiased components in DSS. This integer value represent the
        number of components to keep.
        :param keep1: float controlling  whitening of unbiased components in DSS. This value will remove components
        below keep1 which is relative to the maximum eigen value.
        :param perc0: float (between 0 and 1) controlling whitening of unbiased components in DSS.
        This value will preserve components that explain the percentage of variance.
        :param perc1: float (between 0 and 1) controlling the number of biased components kept in DSS.
        This value will preserve the components of the biased PCA analysis that explain the percentage of variance.
        :param block_size: integer indicating the number of trials that would be used to estimate the weights
        :param n_tracked_points: number of equally spaced points over time used to estimate residual noise and weights
        :param delta_frequency: frequency size around each sf_join_frequency to estimate noise
        :param n_jobs: number of CPUs to compute FFT
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(SpatialFilter, self).__init__(input_process=input_process, **kwargs)
        self.sf_join_frequencies = set_default_unit(sf_join_frequencies, u.Hz)
        self.demean_data = demean_data
        self.weight_data = weight_data
        self.weighted_frequency_domain = weighted_frequency_domain
        self.weight_across_epochs = weight_across_epochs
        self.pwr0 = None
        self.pwr1 = None
        self.n_components_rotation_1 = None
        self.n_components_rotation_2 = None
        self.n_possible_components = None
        self.cov = None
        self.keep0 = keep0
        self.keep1 = keep1
        self.perc0 = perc0
        self.perc1 = perc1
        self.block_size = block_size
        self.n_tracked_points = n_tracked_points
        self.delta_frequency = delta_frequency
        self.weights = None
        self.n_jobs = n_jobs

    def transform_data(self):
        # compute spatial filter
        z, pwr0, pwr1, cov, n_0, n_1, weights = et_get_spatial_filtering(
            epochs=self.input_node.data,
            fs=self.input_node.fs,
            sf_join_frequencies=self.sf_join_frequencies,
            demean_data=self.demean_data,
            weight_data=self.weight_data,
            weighted_frequency_domain=self.weighted_frequency_domain,
            weight_across_epochs=self.weight_across_epochs,
            weights=self.input_node.w,
            keep0=self.keep0,
            keep1=self.keep1,
            perc0=self.perc0,
            perc1=self.perc1,
            block_size=self.block_size,
            n_tracked_points=self.n_tracked_points,
            delta_frequency=self.delta_frequency,
            n_jobs=self.n_jobs
        )
        self.output_node.data = z * u.dimensionless_unscaled
        self.pwr0 = pwr0
        self.pwr1 = pwr1
        self.cov = cov
        self.n_components_rotation_1 = n_0
        self.n_components_rotation_2 = n_1
        self.n_possible_components = self.input_node.data.shape[1]
        self.weights = weights


class ApplySpatialFilter(InputOutputProcess):
    def __init__(self,
                 input_process: SpatialFilter | None = None,
                 sf_components: np.array = np.array([]),
                 sf_thr: float = 0.8,
                 **kwargs):
        """
        This class will apply an SpatialFilter to the data. If sf_components are paased, only those will be used to
        filter the data
        :param input_process: an SpatialFilter InputOutputProcess Class
        :param sf_components: numpy array of integers with indexes of components to be kept
        :param sf_thr: float indicating the percentage of explained variance by components to be kept (this is used when
        sf_components is empty)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ApplySpatialFilter, self).__init__(input_process=input_process, **kwargs)
        self.sf_components = sf_components
        self.sf_thr = sf_thr
        self.kept_components = None

    def transform_data(self):
        filtered_data, components_idx = et_apply_spatial_filtering(z=self.input_node.data,
                                                                   pwr0=self.input_process.pwr0,
                                                                   pwr1=self.input_process.pwr1,
                                                                   cov_1=self.input_process.cov,
                                                                   sf_components=self.sf_components,
                                                                   sf_thr=self.sf_thr)
        self.output_node.data = filtered_data
        self.kept_components = components_idx


class CreateAndApplySpatialFilter(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 sf_join_frequencies: np.array([u.Quantity]) = None,
                 sf_components=np.array([]),
                 sf_thr: float = 0.8,
                 keep0: int | None = None,
                 keep1: float = 1e-9,
                 perc0: float = 1.0,
                 perc1: float | None = None,
                 test_frequencies: np.array([u.Quantity]) = None,
                 delta_frequency: u.Quantity = 5 * u.Hz,
                 block_size: int = 10,
                 n_tracked_points: int | None = None,
                 demean_data: bool = True,
                 weight_data: bool = True,
                 weighted_frequency_domain: bool = False,
                 weight_across_epochs: bool = True,
                 projection_domain: Domain = Domain.time,
                 components_to_plot: np.array = np.arange(0, 10),
                 plot_projections: bool = True,
                 plot_power: bool = True,
                 plot_x_lim: type([float, float]) = None,
                 plot_y_lim: type([float, float]) = None,
                 user_naming_rule: str | None = None,
                 fig_format: str = '.png',
                 return_figures: bool = False,
                 save_to_file: bool = True,
                 n_jobs: int = 1,
                 **kwargs):
        """
        This class will create and apply a spatial filter to the data.
        :param input_process: an InputOutputProcess Class
        :param sf_join_frequencies: numpy array indicating the biased frequencies (useful for steady-state responses)
        :param sf_components: numpy array of integers with indexes of components to be kept
        :param sf_thr: float indicating the percentage of explained variance by components to be kept (this is used when
        sf_components is empty)
        :param keep1: float controlling  whitening of unbiased components in DSS. This value will remove components
        below keep1 which is relative to the maximum eigen value.
        :param perc0: float (between 0 and 1) controlling whitening of unbiased components in DSS.
        This value will preserve components that explain the percentage of variance.
        :param perc1: float (between 0 and 1) controlling the number of biased components kept in DSS.
        This value will preserve the components of the biased PCA analysis that explain the percentage of variance.
        :param test_frequencies: frequency array to compute statistics in the frequency-domain in the component space.
        :param delta_frequency: frequency size around each sf_join_frequency to estimate noise
        :param demean_data: If true, filter will be created with demeaned data
        :param weight_data: if true, weighted average will be use to create the filter
        :param weighted_frequency_domain: boll indicating if the weghts are compute in the time or frequency domain
        :param weight_across_epochs: if True, weights are computed across epochs (as in Elbeling 1984) otherwise weights
        are computed within epoch (1 / variance across time)
        :param projection_domain: indicate the domain in which component will be projected in plots
        :param components_to_plot: numpy array indicating which components will be plotted.
        :param plot_projections: if true, components will be projected to the original space and plots will be generated
        :param plot_power: if true both bias and unbiased component's power as well as their rations will be plotted
        :param plot_x_lim: list with minimum and maximum horizontal range of x axis
        :param plot_y_lim: list with minimum and maximum vertical range of y axis
        :param user_naming_rule: string indicating a user naming to be included in the figure file name
        :param fig_format: string indicating the format of the output figure (e.g. '.png' or '.pdf')
        :param return_figures: bool indicating if figure handle should be returned in self.figures
        :param save_to_file: bool indicating whether figure should be saved to file
        :param block_size: number of trials that will be stacked together to estimate the residual noise
        :param n_tracked_points: number of equally spaced points over time used to estimate residual noise and weights
        n_tracked_points
        :param n_jobs: number of CPUs for fft
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(CreateAndApplySpatialFilter, self).__init__(input_process=input_process, **kwargs)
        self.sf_join_frequencies = set_default_unit(sf_join_frequencies, u.Hz)
        self.sf_components = sf_components
        self.sf_thr = sf_thr
        self.keep0 = keep0
        self.keep1 = keep1
        self.perc0 = perc0
        self.perc1 = perc1
        self.p_ratio = None
        self.pwr0 = None
        self.pwr1 = None
        self.kept_components = None
        self.test_frequencies = test_frequencies
        self.delta_frequency = delta_frequency
        self.block_size = block_size
        self.n_tracked_points = n_tracked_points
        self.weights = None
        self.components_to_plot = components_to_plot
        self.plot_projections = plot_projections
        self.plot_power = plot_power
        self.projection_domain = projection_domain
        self.demean_data = demean_data
        self.weight_data = weight_data
        self.weighted_frequency_domain = weighted_frequency_domain
        self.weight_across_epochs = weight_across_epochs
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.user_naming_rule = user_naming_rule
        self.fig_format = fig_format
        self.return_figures = return_figures
        self.save_to_file = save_to_file
        self.n_jobs = n_jobs
        self.__kwargs = kwargs

    def transform_data(self):
        figures = None
        if self.test_frequencies is None:
            self.test_frequencies = self.sf_join_frequencies
        if self.return_figures:
            figures = []
        spatial_filter = SpatialFilter(input_process=self.input_process,
                                       sf_join_frequencies=self.sf_join_frequencies,
                                       demean_data=self.demean_data,
                                       weight_data=self.weight_data,
                                       weighted_frequency_domain=self.weighted_frequency_domain,
                                       weight_across_epochs=self.weight_across_epochs,
                                       keep0=self.keep0,
                                       keep1=self.keep1,
                                       perc0=self.perc0,
                                       perc1=self.perc1,
                                       block_size=self.block_size,
                                       n_tracked_points=self.n_tracked_points,
                                       delta_frequency=self.delta_frequency,
                                       n_jobs=self.n_jobs
                                       )
        spatial_filter.run()
        filtered_data = ApplySpatialFilter(input_process=spatial_filter,
                                           sf_components=self.sf_components,
                                           sf_thr=self.sf_thr,
                                           **self.__kwargs)
        filtered_data.run()

        self.output_node = filtered_data.output_node
        self.p_ratio = spatial_filter.pwr1 / spatial_filter.pwr0
        self.pwr0 = spatial_filter.pwr0
        self.pwr1 = spatial_filter.pwr1
        self.kept_components = filtered_data.kept_components
        self.weights = spatial_filter.weights

        if self.components_to_plot is not None:
            plotter_1 = PlotSpatialFilterComponents(spatial_filter,
                                                    plot_x_lim=self.plot_x_lim,
                                                    plot_y_lim=self.plot_y_lim,
                                                    user_naming_rule=self.user_naming_rule,
                                                    fig_format=self.fig_format,
                                                    components_to_plot=self.components_to_plot,
                                                    domain=self.projection_domain,
                                                    return_figures=self.return_figures,
                                                    save_to_file=self.save_to_file,
                                                    test_frequencies=self.test_frequencies
                                                    )
            plotter_1.run()
            if self.return_figures:
                figures.append(plotter_1.figures)
            if self.plot_projections and self.save_to_file:
                plotter_2 = ProjectSpatialComponents(spatial_filter,
                                                     user_naming_rule=self.user_naming_rule,
                                                     plot_x_lim=self.plot_x_lim,
                                                     plot_y_lim=self.plot_y_lim,
                                                     components_to_plot=self.components_to_plot,
                                                     domain=self.projection_domain,
                                                     test_frequencies=self.test_frequencies,
                                                     return_figures=self.return_figures
                                                     )
                plotter_2.run()
                if self.return_figures:
                    figures += plotter_2.figures
        if self.plot_power:
            _fig_power = self.plot_component_power()
            if self.return_figures:
                figures.append(_fig_power)

        self.figures = figures

        dss_data = []
        p_ratio = spatial_filter.pwr1 / spatial_filter.pwr0

        for _component in np.arange(0, spatial_filter.pwr0.size).astype(int):
            _dss_data = DSSData(
                bias_frequencies=str(self.sf_join_frequencies) if self.sf_join_frequencies is not None else None,
                bias_domain=self.projection_domain,
                unbiased_power=spatial_filter.pwr0[_component],
                biased_power=spatial_filter.pwr1[_component],
                total_unbiased_power=np.sum(spatial_filter.pwr0),
                total_biased_power=np.sum(spatial_filter.pwr1),
                n_components_rotation_1=spatial_filter.n_components_rotation_1,
                n_components_rotation_2=spatial_filter.n_components_rotation_2,
                threshold=self.sf_thr,
                component_rank=_component,
                power_ratio=p_ratio[_component] / np.sum(p_ratio),
                kept=bool(np.isin(_component, filtered_data.kept_components)),
                n_possible_components=spatial_filter.n_possible_components,
                main_channel=None)
            dss_data.append(_dss_data)
        dss_table = pd.DataFrame([_data.__dict__ for _data in dss_data])
        self.output_node.processing_tables_local = Tables(table_name=FilterType.dss,
                                                          data=dss_table,
                                                          data_source=self.name)

    def plot_component_power(self):
        inch = 2.54
        fig = plt.figure()
        fig.set_size_inches(18 / inch, 24 / inch)
        gs = gridspec.GridSpec(3, 1)
        ax = plt.subplot(gs[0, 0])
        _normalized_raw_power = self.pwr0 / np.sum(self.pwr0)
        _normalized_evoked_power = self.pwr1 / np.sum(self.pwr1)

        ax.plot(_normalized_raw_power, marker='o', label='Raw')
        ax.plot(_normalized_evoked_power, marker='o', label='Evoked')
        ax.plot(self.kept_components,
                _normalized_evoked_power[self.kept_components],
                marker='*', label='Kept', linestyle='None')
        ax.axvline(self.kept_components.max(), color='black', label=None)
        ax.set_xlabel('Component rank')
        ax.legend(loc="upper right")
        ax.set_title('Normalized Power')

        ax = plt.subplot(gs[1, 0])

        _accumulated_raw_power = np.cumsum(self.pwr0 / np.sum(self.pwr0))
        _accumulated_evoked_power = np.cumsum(self.pwr1) / np.sum(self.pwr1)
        ax.plot(_accumulated_raw_power, marker='o', label='Raw')
        ax.plot(_accumulated_evoked_power, marker='o', label='Evoked')
        ax.plot(self.kept_components,
                _accumulated_evoked_power[self.kept_components],
                marker='*', label='Kept', linestyle='None')
        ax.axvline(self.kept_components.max(), color='black', label=None)
        ax.set_ylim([0, 1])
        ax.set_xlabel('Component rank')
        ax.set_title('Accumulated power')
        ax.legend(loc="upper right")

        ax = plt.subplot(gs[2, 0])
        _per_component_explained_power = (self.pwr1 / self.pwr0) / np.sum(self.pwr1 / self.pwr0)
        _accumulated_component_explained_power = (np.cumsum(self.pwr1) / np.cumsum(self.pwr0)) / np.sum(
            self.pwr1 / self.pwr0)
        ax.plot(_per_component_explained_power,
                marker='o',
                label='Per component')
        ax.plot(_accumulated_component_explained_power,
                marker='o',
                label='Accumulated')
        ax.plot(self.kept_components,
                _per_component_explained_power[self.kept_components],
                marker='*', label='Kept', linestyle='None')
        ax.axvline(self.kept_components.max(), color='black', label=None)
        # ax.set_ylim([0, 1])
        ax.set_xlabel('Component rank')
        ax.set_title('Evoked power per component / Total power')
        ax.legend(loc="upper right")

        _sep = '_' if self.user_naming_rule is not None else ''
        _naming_rule = '' if self.user_naming_rule is None else self.user_naming_rule
        _figure_basename = self.name + _sep + _naming_rule
        _fig_path = self.output_node.paths.figures_current_dir + _figure_basename + 'components_power' + self.fig_format
        fig.tight_layout()
        fig.savefig(_fig_path)
        print('figure saved: {:}'.format(_fig_path))
        return fig


class PlotSpatialFilterComponents(InputOutputProcess):
    def __init__(self, input_process=SpatialFilter,
                 components_to_plot: np.array = np.arange(0, 10),
                 domain: Domain = Domain.time,
                 test_frequencies: type(u.Quantity) | None = None,
                 user_naming_rule: str = 'components',
                 plot_x_lim: [float, float] = None,
                 plot_y_lim: [float, float] = None,
                 fig_format: str = '.png',
                 return_figures: bool = False,
                 save_to_file: bool = True,

                 **kwargs):
        """
        This class plots the components waveforms (from an SpatialFilter)
        :param input_process: anInputOutputProcess Class
        :param components_to_plot: numpy array indicating which components will be plotted.
        :param domain: indicate the domain in which component will be projected
        :param user_naming_rule: string indicating a user naming to be included in the figure file name
        :param plot_x_lim: list with minimum and maximum horizontal range of x axis
        :param plot_y_lim: list with minimum and maximum vertical range of y axis
        :param fig_format: string indicating the format of the output figure (e.g. '.png' or '.pdf')
        :param return_figures: bool indicating if figure should be returned in self.figures
        :param save_to_file: bool indicating whether figure should be saved to file
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(PlotSpatialFilterComponents, self).__init__(input_process=input_process, **kwargs)
        self.components_to_plot = components_to_plot
        self.domain = domain
        self.test_frequencies = test_frequencies
        self.user_naming_rule = user_naming_rule
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.fig_format = fig_format
        self.return_figures = return_figures
        self.save_to_file = save_to_file
        self.__kwargs = kwargs

    def transform_data(self):
        if self.components_to_plot is not None:
            # we copy the input process to overwrite the layout without affecting other pipe processes
            _input_process = copy.deepcopy(self.input_process)

            # _input_process.output_node.y_units = u.def_unit('A.U.')
            # generate a generic layout
            _input_process.output_node.layout = np.array([ChannelItem()
                                                          for _ in range(_input_process.output_node.data.shape[1])])
            for _i, _lay in enumerate(_input_process.output_node.layout):
                _lay.label = str(_i)

            if self.domain == Domain.time:
                average = AverageEpochs(_input_process)

            if self.domain == Domain.frequency:
                average = AverageEpochsFrequencyDomain(_input_process,
                                                       test_frequencies=self.test_frequencies,
                                                       delta_frequency=self.input_process.delta_frequency,
                                                       weight_frequencies=self.test_frequencies
                                                       )
            average.name = 'AveragedSpatialComponents'
            average.run()
            plotter = PlotWaveforms(average,
                                    user_naming_rule='{:}_{:}_components'.format(
                                        self.user_naming_rule,
                                        average.output_node.data.shape[1]),
                                    ch_to_plot=self.components_to_plot,
                                    plot_x_lim=self.plot_x_lim,
                                    plot_y_lim=None,
                                    fig_format=self.fig_format,
                                    return_figures=self.return_figures,
                                    save_to_file=self.save_to_file)
            plotter.run()
            self.figures = plotter.figures


class ProjectSpatialComponents(InputOutputProcess):
    def __init__(self, input_process=SpatialFilter,
                 components_to_plot: np.array = np.arange(0, 10),
                 user_naming_rule: str | None = None,
                 plot_x_lim: [float, float] = None,
                 plot_y_lim: [float, float] = None,
                 domain: Domain = Domain.time,
                 test_frequencies: type(u.Quantity) | None = None,
                 return_figures: bool = False,
                 **kwargs):
        """
        This class will project back to the sensor space each component and plot them in a topographic map.
        :param input_process: an SpatialFilter InputOutputProcess Class
        :param components_to_plot: numpy array indicating which components will be plotted.
        :param user_naming_rule: string indicating a user naming to be included in the figure file name
        :param plot_x_lim: list with minimum and maximum horizontal range of x axis
        :param plot_y_lim: list with minimum and maximum vertical range of y axis
        :param domain: indicate the domain in which component will be projected
        :param test_frequencies: numpy array with frequencies that will be used to compute statistics
        :param return_figures: if true, figures will be returned in self.figures
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ProjectSpatialComponents, self).__init__(input_process=input_process, **kwargs)
        self.components_to_plot = components_to_plot
        self.user_naming_rule = user_naming_rule
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.domain = domain
        self.test_frequencies = set_default_unit(test_frequencies, u.Hz)
        self.return_figures = return_figures
        self.__kwargs = kwargs

    def transform_data(self):
        figures = []
        for _component in self.components_to_plot:
            if _component > self.input_process.output_node.data.shape[1] - 1:
                continue
            if isinstance(self.input_process, SpatialFilter):
                projected_component = ApplySpatialFilter(input_process=self.input_process,
                                                         sf_components=np.array([_component]))
            if isinstance(self.input_process, SpatialFilterICA):
                projected_component = ApplySpatialFilterICA(input_process=self.input_process,
                                                            sf_components=np.array([_component]))
            print('Projecting individual component {:} to sensor space'.format(_component))
            projected_component.run()
            if self.domain == Domain.time:
                average = AverageEpochs(projected_component)
            if self.domain == Domain.frequency:
                average = AverageEpochsFrequencyDomain(projected_component,
                                                       test_frequencies=self.test_frequencies,
                                                       weight_frequencies=self.input_process.sf_join_frequencies,
                                                       delta_frequency=self.input_process.delta_frequency)
            average.run()
            times = None
            if self.domain == Domain.time:
                max_chan = np.argmax(np.std(average.output_node.data, axis=0))
                cha_max_pow_label = average.output_node.layout[max_chan].label
                # find max and min within plot_x_lim
                if self.plot_x_lim is not None:
                    self.plot_x_lim = set_default_unit(self.plot_x_lim, average.output_node.x.unit)
                    _samples = average.output_node.x_to_samples(self.plot_x_lim)
                    _max = np.argmax(average.output_node.data[_samples[0]: _samples[-1], max_chan]) + _samples[0]
                    _min = np.argmin(average.output_node.data[_samples[0]: _samples[-1], max_chan]) + _samples[0]
                else:
                    _max = np.argmax(average.output_node.data[:, max_chan])
                    _min = np.argmin(average.output_node.data[:, max_chan])
                times = np.sort(average.output_node.x[np.array([_max, _min])])
            if self.domain == Domain.frequency:
                if self.input_process.sf_join_frequencies is not None:
                    _idx_f = average.output_node.x_to_samples(self.input_process.sf_join_frequencies)
                    max_chan = np.argmax(np.max(np.abs(average.output_node.data[_idx_f, :]), axis=0))
                    cha_max_pow_label = average.output_node.layout[max_chan].label
                else:
                    _idx_ch = np.argmax(average.output_node.snr)
                    cha_max_pow_label = average.output_node.layout[_idx_ch].label

            # plot time potential fields for average channel
            _sep = '_' if self.user_naming_rule is not None else ''
            _naming_rule = '' if self.user_naming_rule is None else self.user_naming_rule
            plotter = PlotTopographicMap(average,
                                         user_naming_rule=_naming_rule + _sep + 'component_{:}'.format(
                                             _component),
                                         topographic_channels=np.array([cha_max_pow_label]),
                                         plot_x_lim=self.plot_x_lim,
                                         plot_y_lim=self.plot_y_lim,
                                         return_figures=self.return_figures,
                                         title='Component {:}'.format(_component),
                                         times=times)
            plotter.run()
            if self.return_figures and plotter.figures is not None:
                figures += plotter.figures
        self.figures = figures


class CreateAndApplyICAFilter(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 sf_components=np.array([]),
                 sf_thr=0.8,
                 components_to_plot: np.array = np.arange(0, 10),
                 plot_x_lim: [float, float] = None,
                 plot_y_lim: [float, float] = None,
                 n_tracked_points=None,
                 block_size=5,
                 weight_data=True,
                 user_naming_rule: str = '',
                 fig_format: str = '.png',
                 return_figures: bool = False,
                 **kwargs):
        """
        This class will create and apply an ICA filter to the data.
        :param input_process: an InputOutputProcess Class
        :param sf_components: numpy array of integers with indexes of components to be kept
        :param sf_thr: float indicating the percentage of explained variance by components to be kept (this is used when
        sf_components is empty)
        :param components_to_plot: numpy array indicating which components will be plotted.
        :param plot_x_lim: list with minimum and maximum horizontal range of x axis
        :param plot_y_lim: list with minimum and maximum vertical range of y axis
        :param user_naming_rule: string indicating a user naming to be included in the figure file name
        :param fig_format: string indicating the format of the output figure (e.g. '.png' or '.pdf')
        :param return_figures: if True, figures handles will be returnted on self.figures
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(CreateAndApplyICAFilter, self).__init__(input_process=input_process, **kwargs)
        self.sf_components = sf_components
        self.sf_thr = sf_thr
        self.components_to_plot = components_to_plot
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.user_naming_rule = user_naming_rule
        self.fig_format = fig_format
        self.return_figures = return_figures
        self.n_tracked_points = n_tracked_points
        self.block_size = block_size
        self.weight_data = weight_data
        self._unmixing = None
        self._mixing: type(np.array) | None = None
        self._pwr: type(np.array) | None = None
        self._components: type(np.array) | None = None
        self._whitening_m: type(np.array) | None = None
        self.__kwargs = kwargs

    def transform_data(self):
        spatial_filter = SpatialFilterICA(input_process=self.input_process)
        spatial_filter.run()
        print('applying ICA filter')
        filtered_data = ApplySpatialFilterICA(input_process=spatial_filter,
                                              sf_components=self.sf_components,
                                              sf_thr=self.sf_thr,
                                              **self.__kwargs)
        filtered_data.run()
        self.output_node = filtered_data.output_node

        if self.components_to_plot is not None:
            plotter = PlotSpatialFilterComponents(spatial_filter,
                                                  plot_x_lim=self.plot_x_lim,
                                                  plot_y_lim=self.plot_y_lim,
                                                  user_naming_rule=self.user_naming_rule,
                                                  fig_format=self.fig_format,
                                                  components_to_plot=self.components_to_plot
                                                  )
            plotter.run()

            plotter = ProjectSpatialComponents(spatial_filter,
                                               user_naming_rule=self.user_naming_rule,
                                               plot_x_lim=self.plot_x_lim,
                                               plot_y_lim=self.plot_y_lim,
                                               components_to_plot=self.components_to_plot
                                               )
            plotter.run()


class SpatialFilterICA(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 **kwargs):
        """
        This class will create an spatial filter based on the data.
        :param input_process:  InputOutputProcess Class
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(SpatialFilterICA, self).__init__(input_process=input_process, **kwargs)
        self.mixing = None
        self.unmixing = None
        self.pwr = None
        self.whitening_m = None
        self.epoch_size = None

    def transform_data(self):
        # compute spatial filter
        _data = self.input_node.data
        self.epoch_size = _data.shape[0]
        if self.input_node.data.ndim == 3:
            _data = et_unfold(self.input_node.data)
        components, unmixing, mixing, pwr, whitening_m = et_ica_epochs(data=_data,
                                                                       tol=1e-4,
                                                                       iterations=10)
        self.mixing = mixing
        self.unmixing = unmixing
        self.pwr = pwr
        self.whitening_m = whitening_m
        self.output_node.data = et_fold(components, epoch_size=self.epoch_size)


class ApplySpatialFilterICA(InputOutputProcess):
    def __init__(self, input_process: SpatialFilterICA | None = None,
                 sf_components: np.array = np.array([]),
                 sf_thr: float = 0.8,
                 **kwargs):
        """
        This class will apply an SpatialFilter to the data. If sf_components are paased, only those will be used to
        filter the data
        :param input_process: an SpatialFilter InputOutputProcess Class
        :param sf_components: numpy array of integers with indexes of components to be kept
        :param sf_thr: float indicating the percentage of explained variance by components to be kept (this is used when
        sf_components is empty)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ApplySpatialFilterICA, self).__init__(input_process=input_process, **kwargs)
        self.sf_components = sf_components
        self.sf_thr = sf_thr

    def transform_data(self):
        print('applying spatial filter')
        if self.sf_components is None or not self.sf_components.size:
            cumpower = np.cumsum(self.input_process.pwr) / np.sum(self.input_process.pwr)
            n_idxs = np.argwhere(cumpower <= self.sf_thr)
            n_components = np.arange(n_idxs.size)
        else:
            n_components = self.sf_components

        clean_epochs = self.mix_components(components_idx=n_components)
        if self.input_process.epoch_size is not None:
            clean_epochs = et_fold(clean_epochs, epoch_size=self.input_process.epoch_size)
        self.output_node.data = clean_epochs

    def mix_components(self,
                       components_idx: type(np.array) | None = None):
        w_c = np.zeros(self.input_process.mixing.shape)
        w_c[:, components_idx] = 1
        s_clean = self.input_process.mixing * w_c
        _components = et_unfold(self.input_process.output_node.data)
        clean_data = s_clean.dot(_components.T).T
        return clean_data
