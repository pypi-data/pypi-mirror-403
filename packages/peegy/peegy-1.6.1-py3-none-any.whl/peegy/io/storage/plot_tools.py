import copy
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from peegy.layouts.layouts import Layout
from peegy.plot import eeg_plot_tools as eegpt
import matplotlib as mpl
from matplotlib import ticker
from astropy import units as u
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from typing import List
from peegy.definitions.channel_definitions import Domain
from peegy.io.storage.data_storage_reading_tools import (sqlite_tables_to_pandas, sqlite_all_waveforms_to_pandas,
                                                         group_waveforms_df_by)
__author__ = 'jundurraga'


def has_twin(ax: plt.Axes | None = None):
    """
    Check if input axis has twin axis
    :param ax:
    :return: bool indicating whether twin axis is present or not
    """
    for other_ax in ax.figure.axes:
        if other_ax is ax:
            continue
        if other_ax.bbox.bounds == ax.bbox.bounds:
            return True
    return False


def merge_waveforms_by(df: pd.DataFrame | None = None, group_by: list[str] | None = None):
    """
    This function will pool together the waveforoms from different rows in a dataframe
    :param df: pandas data frame
    :param group_by: grouping keys in dataframe
    :return: pandas dataframe with grouped waveforms
    """
    groups = df.groupby(group_by,
                        observed=False,
                        as_index=False,
                        sort=False)
    output = pd.DataFrame()
    for _id, (_group_keys, _group) in enumerate(groups):
        if not _group.size:
            continue
        _current_group = _group.iloc[[0]].copy()
        _data = np.array([])
        for _, _current_sub_row in _group.iterrows():
            _new_data = _current_sub_row['y']
            if _new_data.ndim == 1:
                _new_data = _new_data[:, None]
            if not _data.size:
                _data = _new_data
            else:
                _data = np.hstack([_data, _new_data])
        print('group {:} output shape {:}'.format(_group_keys, _data.shape))
        _current_group['y'] = _current_group['y'].apply(lambda x: _data)
        output = pd.concat([output, _current_group], ignore_index=True)
    return output


def plot_time_frequency_responses(dataframe: pd.DataFrame | None = None,
                                  rows_by: str | None = None,
                                  cols_by: str | None = None,
                                  color_map: str = 'viridis',
                                  sub_average_time_buffer_size: int | None = None,
                                  time_xlim: type([float, float]) = None,
                                  time_ylim: type([float, float]) = None,
                                  freq_xlim: type([float, float]) = None,
                                  freq_ylim: type([float, float]) = None,
                                  time_vmarkers: type(np.array) | None = None,
                                  freq_vmarkers: type(np.array) | None = None,
                                  freq_vmarkers_style: str | None = None,
                                  show_individual_waveforms: bool = True,
                                  individual_waveforms_alpha: float = 0.1,
                                  show_mean: bool = True,
                                  show_sem: bool = False,
                                  sem_alpha: float = 0.2,
                                  show_sd: bool = True,
                                  sd_alpha: float = 0.2,
                                  show_legend: bool = True,
                                  legend_location='upper center',
                                  title_by: str = 'row',
                                  title_v_offset: float = 0.0,
                                  ylabel: str | None = None,
                                  y_unit_to: u.Unit | None = None,
                                  x_unit_to: u.Unit | None = None,
                                  inset_y_unit_to: u.Unit | None = None,
                                  inset_x_unit_to: u.Unit | None = None,
                                  fontsize: float = 6,
                                  group_by: list[str] | None = None,
                                  colour_by: list[str] | None = None,
                                  show_column_labels: bool = True,
                                  insets_col_source: str | None = None,
                                  insets_col_value: str | None = None,
                                  insets_position: [float, float, float, float] = None,
                                  ) -> plt.figure:
    """
    This function will plot the waveforms contained in a pandas dataframe read using the sqlite_waveforms_to_pandas
    function of pEEGy.
    The rows and columns of the output plot are specified by the factors of the dataframe.
    The output will show the data for each of those factors (both individual and average data).
    :param dataframe: a pandas dataframe returned by sqlite_waveforms_to_pandas function of pEEGy
    :param rows_by: name of the factor in the dataframe for which the rows in the plot will be split
    :param cols_by: name of the factor in the dataframe for which the columns in the plot will be split
    :param color_map: name of matplotlib colormap (e.g. 'viridis', 'Spectral', 'coolwarm', etcetera
    :param sub_average_time_buffer_size: This is a parameter used to sub_average time_domain data. For example, if each
    of your data have 10000 points, and you want to show the average having a length of 1000 samples, you could specify
    sub_average_time_buffer_size = 1000. This will averaged the 10000 points by splitting the data into blocks of 1000
    samples
    :param time_xlim: x axis limit for the time-domain panels
    :param time_ylim: y axis limit for the time-domain panels
    :param freq_xlim: x axis limit for the frequency-domain panels
    :param freq_ylim: y axis limit for the frequency-domain panels
    :param time_vmarkers: array with x values to add a vertical marker in the time-domain panels
    :param freq_vmarkers: array with x values to add a vertical marker in the frequency-domain panels
    :param show_individual_waveforms: if true, individual waveforms will be shown.
    :param individual_waveforms_alpha: value between 0 and 1 indicating the alpha level of individual waveforms
    :param show_mean: if true, the mean across conditions will be shown
    :param show_sem: if true, the standard error of the mean will be shown
    :param sem_alpha: value between 0 and 1 indicating the alpha level of the sem
    :param show_sd: if true, the standard deviation of the mean will be shown
    :param sd_alpha: value between 0 and 1 indicating the alpha level of the standard deviation
    :param show_legend: if True, the legend for any other category present in the dataframe will be shown
    :param title_by: string specifying from which factor you want to show the titles in each panel. This can be: "row",
    "col", or "both"
    :param title_v_offset: float specifying the vertical offset of the title
    :param freq_vmarkers_style: style of the marker in the frequency-domain. If not passed, vertical lines are used.
    :param ylabel: Label to put in the vertical axis. If empty, the Amplitude and unit of it are used.
    :param y_unit_to: Specify the units in which the vertical axis will be displayed
    :param x_unit_to: Specify the units in which the horizontal axis will be displayed
    :param fontsize: the font size
    :param group_by: list of keys in dataframe which will be grouped and coded by colour
    :param show_column_labels: bool indicatint whether the columns labels should be shown
    :return:
    """
    df = copy.copy(dataframe)
    df.reset_index(inplace=True, drop=True)
    _rows_and_cols = []
    row_conditions = np.array([''])
    col_conditions = np.array([''])
    if rows_by is not None:
        _rows_and_cols.append(rows_by)
        row_conditions = df[rows_by].astype("category").cat.categories
        row_domains = df.iloc[df[rows_by].index]['domain'].unique()
        unique_row_domains = row_domains.size == 1
        n_rows = row_conditions.size
    else:
        df.loc[:, 'dummy_row'] = ''
        _rows_and_cols.append('dummy_row')
        row_domains = df['domain'].unique()
        unique_row_domains = row_domains.size == 1
        n_rows = 1
    idx_rows = np.arange(row_conditions.size)
    if cols_by is not None:
        _rows_and_cols.append(cols_by)
        col_conditions = df[cols_by].astype("category").cat.categories
        # col_domains = df.iloc[df[cols_by].index]['domain'].unique()
        # unique_col_domains = col_domains.size == 1
        n_cols = col_conditions.size
    else:
        df.loc[:, 'dummy_col'] = ''
        _rows_and_cols.append('dummy_col')
        # col_domains = df['domain'].unique()
        # unique_col_domains = row_domains.size == 1
        n_cols = 1
    idx_cols = np.arange(col_conditions.size)
    _x_unit_to = x_unit_to
    _y_unit_to = y_unit_to

    # set colurs from colormap
    df['dummy_color_categories'] = ''
    iterate_by = None
    new_var = pd.Series(df.loc[:, ['dummy_color_categories']].values[:, 0])
    if group_by is None:
        n_colors = 1
        unique_color_factors = np.array([''])
    else:
        iterate_by = group_by
        if colour_by is not None:
            iterate_by = colour_by
        for _col_name in iterate_by:
            new_var = new_var + df[_col_name].values.astype(str)
        df['dummy_color_categories'] = new_var
        for _col_name in iterate_by:
            df[_col_name] = pd.Categorical(df[_col_name])
        # sort to keep factor order in colours
        df.sort_values(by=iterate_by, inplace=True)
        vals, idx = np.unique(df['dummy_color_categories'], return_index=True)
        unsorted_unique = vals[np.argsort(idx)]

        df['dummy_color_categories'] = pd.Categorical(df['dummy_color_categories'],
                                                      categories=unsorted_unique)
        unique_color_factors = np.array(df['dummy_color_categories'].cat.categories.tolist())

    n_colors = unique_color_factors.size
    cmap = mpl.colormaps[color_map]
    _colors = cmap(np.linspace(0, 1, n_colors))
    _colors = [mpl.colors.to_hex(cmap(i)) for i in range(n_colors)]

    groups = df.groupby(_rows_and_cols, observed=False, sort=True)
    fig_out = plt.figure(constrained_layout=False)
    # set up subplots
    widths = [1.0] * n_cols
    heights = [1.0] * n_rows
    heights.insert(0, 0.01)  # this is for the top labels
    widths.append(0.01)  # this is for the right labels
    gs = fig_out.add_gridspec(ncols=n_cols + 1, nrows=n_rows + 1,
                              width_ratios=widths,
                              height_ratios=heights,
                              )

    all_ax_row_label = []
    all_ax_col_label = []
    # attach all axis to figure to ensure the are all created before calling them
    [plt.subplot(gs[_idx_row, _idx_col]) for _idx_row in range(gs.get_geometry()[0]) for _idx_col in
     range(gs.get_geometry()[1])]

    for _id, ((_current_row_group, _current_col_group), _group) in enumerate(groups):
        if insets_col_source is None:
            _current_group = _group
        else:
            _current_group = _group[_group[insets_col_source] != insets_col_value]

        if group_by is not None:
            _current_group = merge_waveforms_by(df=_current_group, group_by=group_by)
        if iterate_by is not None:
            _current_group.sort_values(by=iterate_by, inplace=True)
        _inset_df = None
        if insets_col_source is not None and insets_col_value is not None:
            _inset_df = _group[_group[insets_col_source] == insets_col_value]

        _idx_row = idx_rows[_current_row_group == row_conditions].squeeze() + 1
        _idx_col = idx_cols[_current_col_group == col_conditions].squeeze()

        _columns_legends = []
        for _col in _current_group:
            _filter = _current_group[_col].apply(lambda x:
                                                 not (isinstance(x, str) or
                                                      isinstance(x, float) or
                                                      isinstance(x, int)))
            if np.any(_filter.values):
                continue
            if colour_by is not None:
                if _col in colour_by:
                    _columns_legends.append(_col)
            else:
                if group_by is not None:
                    if _col in group_by:
                        _columns_legends.append(_col)
                elif len(_current_group[_col].unique()) > 1:
                    _columns_legends.append(_col)

        ax = plt.subplot(gs[_idx_row, _idx_col])
        _last_col_ax = plt.subplot(gs[_idx_row, n_cols])
        for _i, (_, _row) in enumerate(_current_group.iterrows()):
            # get color index
            _color_index,  = np.where(_row['dummy_color_categories'] == unique_color_factors)
            _color_index = int(_color_index)

            _row_summary = add_waveforms_to_df(
                _row=_row,
                _y_unit_to=y_unit_to,
                _x_unit_to=x_unit_to,
                sub_average_time_buffer_size=sub_average_time_buffer_size
            )

            set_axis(ax=ax,
                     _row=_row_summary,
                     _columns_legends=_columns_legends,
                     _current_row_group=_current_row_group,
                     _current_col_group=_current_col_group,
                     _idx_row=_idx_row,
                     time_xlim=time_xlim,
                     time_ylim=time_ylim,
                     freq_xlim=freq_xlim,
                     freq_ylim=freq_ylim,
                     time_vmarkers=time_vmarkers,
                     freq_vmarkers=freq_vmarkers,
                     freq_vmarkers_style=freq_vmarkers_style,
                     show_individual_waveforms=show_individual_waveforms,
                     individual_waveforms_alpha=individual_waveforms_alpha,
                     show_mean=show_mean,
                     show_sem=show_sem,
                     sem_alpha=sem_alpha,
                     show_sd=show_sd,
                     sd_alpha=sd_alpha,
                     show_legend=show_legend,
                     title_by=title_by,
                     title_v_offset=title_v_offset,
                     fontsize=fontsize,
                     color=_colors[_color_index],
                     )
        # all_ax_row_label.append(_last_col_ax)
        # set right labels
        _last_col_ax.set_xticks([])
        _last_col_ax.set_yticks([])
        _last_col_ax.axis('off')
        if not has_twin(_last_col_ax):
            ax_row_label = _last_col_ax.twinx()
            ax_row_label.autoscale(enable=False)
            ax_row_label.set_ylabel(_current_row_group,
                                    size=fontsize,
                                    rotation=-90)
            ax_row_label.set_yticklabels([])
            ax_row_label.tick_params(
                axis='y',  # changes apply to the y-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelleft=True,
                labelsize=fontsize)
            ax_row_label.spines['left'].set_visible(False)
            ax_row_label.spines['right'].set_visible(False)
            ax_row_label.spines['top'].set_visible(False)
            ax_row_label.spines['bottom'].set_visible(False)
            ax_row_label.set_xticks([])
            ax_row_label.set_yticks([])
            all_ax_row_label.append(ax_row_label)
        # set top labels
        _first_row_ax = plt.subplot(gs[0, _idx_col])
        _first_row_ax.set_xticks([])
        _first_row_ax.set_yticks([])
        _first_row_ax.axis('off')
        if not has_twin(_first_row_ax):
            ax_col_label = _first_row_ax.twiny()
            ax_col_label.autoscale(enable=False)
            if show_column_labels:
                ax_col_label.set_xlabel(_current_col_group, size=fontsize)
            ax_col_label.set_xticklabels([])
            ax_col_label.tick_params(
                axis='x',  # changes apply to the x-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelleft=True,
                labelsize=fontsize)
            ax_col_label.spines['left'].set_visible(False)
            ax_col_label.spines['right'].set_visible(False)
            ax_col_label.spines['top'].set_visible(False)
            ax_col_label.spines['bottom'].set_visible(False)
            ax_col_label.set_xticks([])
            ax_col_label.set_yticks([])
            all_ax_col_label.append(ax_col_label)
        if inset_axes and _inset_df is not None:
            if insets_position is None:
                _position = [0.7, 0.8, 0.3, 0.2]
            else:
                _position = tuple(insets_position)

            _insets = get_insets(ax)
            if len(_insets) > 0:
                inset_ax = _insets[0]
            else:
                inset_ax = ax.inset_axes(_position,
                                         transform=ax.transAxes)
            if _inset_df.size:
                _current_inset = merge_waveforms_by(df=_inset_df[_i:_i + 1], group_by=insets_col_source).iloc[0]
                _inset_data = add_waveforms_to_df(
                    _row=_current_inset,
                    _y_unit_to=inset_y_unit_to,
                    _x_unit_to=inset_x_unit_to,
                    sub_average_time_buffer_size=sub_average_time_buffer_size
                )

                set_axis(ax=inset_ax,
                         _row=_inset_data,
                         _columns_legends=_columns_legends,
                         _current_row_group=_current_row_group,
                         _current_col_group=_current_col_group,
                         _idx_row=_idx_row,
                         time_xlim=time_xlim,
                         time_ylim=time_ylim,
                         freq_xlim=freq_xlim,
                         freq_ylim=freq_ylim,
                         time_vmarkers=time_vmarkers,
                         freq_vmarkers=freq_vmarkers,
                         freq_vmarkers_style=freq_vmarkers_style,
                         show_individual_waveforms=show_individual_waveforms,
                         individual_waveforms_alpha=individual_waveforms_alpha,
                         show_sem=show_sem,
                         sem_alpha=sem_alpha,
                         show_sd=show_sd,
                         sd_alpha=sd_alpha,
                         show_legend=show_legend,
                         title_by=title_by,
                         title_v_offset=title_v_offset,
                         fontsize=fontsize,
                         color=_colors[_color_index],
                         )
        if _x_unit_to is None:
            _x_unit_to = _row_summary['x_unit']
        if _y_unit_to is None:
            _y_unit_to = _row_summary['y_unit']
    all_axes = fig_out.get_axes()
    axis_with_data = [ax for ax in all_axes if
                      ax not in all_ax_row_label and
                      ax not in all_ax_col_label and
                      ax.has_data()]
    all_axis_with_data = np.all(axis_with_data)
    # check if there is a common legend. If so, then we keep only one across all axes
    _unique_labels = []
    _unique_handles = []
    for _ax in axis_with_data:
        _handles, _labels = _ax.get_legend_handles_labels()
        if len(_handles) > 0 and len(_labels) > 0:
            _unique_handles = _unique_handles + [_handles]
            _unique_labels = _unique_labels + [_labels]
    _unique_handles = [b for b in _unique_handles if b]
    _unique_labels = [b for b in _unique_labels if b]

    common_labels = True
    for _idx_ul in range(len(_unique_labels) - 1):
        diff = set(_unique_labels[_idx_ul]) - set(_unique_labels[_idx_ul + 1])
        if len(diff) > 0:
            common_labels = False
            break
    if common_labels and len(_unique_handles) > 0:
        for _ax in axis_with_data:
            if _ax.legend_ is not None:
                _ax.get_legend().remove()
        _the_labels = _unique_labels[0]
        _the_handles = np.array(_unique_handles[0])
        # keep unique colour catctors
        _, _indices = np.unique(_the_labels, return_index=True)
        _the_labels = [_the_labels[_i] for _i in _indices]
        _the_handles = [_the_handles[_i] for _i in _indices]
        fig_out.legend(_the_handles,
                       _the_labels,
                       loc=legend_location,
                       fontsize=fontsize,
                       frameon=False,
                       ncol=len(_the_labels),
                       handlelength=1
                       )

    if ylabel is None:
        if _y_unit_to is not None:
            fig_out.supylabel('Amplitude [{:}]'.format(_y_unit_to), size=fontsize)
    else:
        fig_out.supylabel(ylabel, size=fontsize)
    if unique_row_domains and all_axis_with_data and np.all(row_domains == Domain.time) and n_cols > 1:
        fig_out.supxlabel('Time [{:}]'.format(_x_unit_to), size=fontsize)
    if unique_row_domains and all_axis_with_data and np.all(row_domains == Domain.frequency) and n_cols > 1:
        fig_out.supxlabel('Frequency [{:}]'.format(_x_unit_to), size=fontsize)

    unique_x_lim_per_row = []
    for _i_col in range(gs.get_geometry()[1] - 1):
        all_axis = [plt.subplot(gs[_i_row, _i_col]) for _i_row in range(1, gs.get_geometry()[0])]
        lims = []
        for _ax in all_axis:
            lims.append(np.array(_ax.get_xlim()))
        unique_x_lim_per_row.append(np.unique(np.array(lims), axis=0).shape[0] == 1)
    unique_x_lim = np.all(unique_x_lim_per_row)

    unique_y_lim_per_col = []
    for _i_row in range(1, gs.get_geometry()[0]):
        all_axis = [plt.subplot(gs[_i_row, _i_col]) for _i_col in range(gs.get_geometry()[1] - 1)]
        lims = []
        for _ax in all_axis:
            if _ax.has_data():
                lims.append(np.array(_ax.get_ylim()))
        unique_y_lim_per_col.append(np.unique(np.array(lims), axis=0).shape[0] == 1)
    unique_y_lim = np.all(unique_y_lim_per_col)
    for ax in all_axes:
        if not ax.has_data() and ax not in all_ax_row_label and ax not in all_ax_col_label:
            ax.set_visible(False)
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_xlabel('')
            continue
        ax.spines['top'].set_visible(False)
        if ax not in all_ax_col_label:
            if unique_row_domains and all_axis_with_data:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_last_row() and ax.has_data():
                    ax.set_xticklabels([])
                    ax.set_xlabel('')
                if n_cols > 1:
                    ax.set_xlabel('')
            elif unique_x_lim:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_last_row() and ax.has_data():
                    ax.set_xticklabels([])
                    ax.set_xlabel('')

            if unique_y_lim:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_first_col() and ax.has_data():
                    ax.set_yticklabels([])
                    ax.set_ylabel('')

        # ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=fontsize)

    inch = 2.54
    fig_out.set_size_inches(12.0 / inch, 2.25 * len(row_conditions) / inch)
    fig_out.subplots_adjust(top=0.98, bottom=0.08, hspace=0.0, left=0.15, right=0.95)
    fig_out.tight_layout()
    return fig_out


def plot_topographic_maps(dataframe: pd.DataFrame | None = None,
                          rows_by: str | None = None,
                          cols_by: str | None = None,
                          subject_id_column: str = 'subject_id',
                          normalize_by: str = 'subject_id',
                          channels_column: str = 'channel',
                          title: str = '',
                          topographic_value: str | None = None,
                          layout: str | None = None,
                          title_by: str | None = None,
                          title_v_offset: float = 0.0,
                          fontsize: float = 6,
                          grid_size: np.complex128 = 600j,
                          color_map_label: str | None = None,
                          normalize: bool = False,
                          show_sensors: bool = True,
                          show_sensor_label: bool = False,
                          n_contour_levels: int = 35,
                          max_topographic_value: float | None = None,
                          min_topographic_value: float | None = None,
                          contour_line_width: float = 0.1,
                          apply_function: object = np.mean,
                          fun_args: dict = {'axis': 2}
                          ) -> plt.figure:
    """
    This function will plot the waveforms contained in a pandas dataframe read using the sqlite_waveforms_to_pandas
    function of pEEGy.
    The rows and columns of the output plot are specified by the factors of the dataframe.
    The output will show the data for each of those factors (both individual and average data)
    :param dataframe: a pandas dataframe returned by sqlite_waveforms_to_pandas function of pEEGy
    :param rows_by: name of the factor in the dataframe for which the rows in the plot will be split
    :param cols_by: name of the factor in the dataframe for which the columns in the plot will be split
    :param subject_id_column: string indicating the column name with subject ids
    :param normalize_by: string indicating the column that will be used to normalized the data
    :param channels_column: name of column containing channel labels
    :param title: title of the figure
    :param topographic_value: name of column containing the value to be shown by the topographic map
    :param layout: path or name of the layout to be used
    :param title_by: string specifying from which factor you want to show the titles in each panel. This can be: "row",
    "col", or "both"
    :param title_v_offset: float specifying the vertical offset of the title
    :param fontsize: the fontsize
    :param grid_size: complex number indicating the size of the grid,
    :param color_map_label: string with the label that would be use of the colourmap. If empty, the default value will
    be the topographic_value
    :param normalize: if True, topographic maps will be normalized within normalize_by
    :param show_sensors: if True, the position of the sensors will be shown
    :param show_sensor_label: if True, the label of the sensor will be shown
    :param n_contour_levels: number of contour lines to plot
    :param min_topographic_value: if given, the colour scale will be restricted to have this value as maximum, otherwise
    it will be determined from the data.
    :param max_topographic_value: if given, the colour scale will be restricted to have this value as minimum, otherwise
    it will be determined from the data.
    :param contour_line_width: float indicating the with (in points) of the contour lines
    :param apply_function: function to be applied to each subgroup
    :param fun_args: extra arguments to be used by apply_function. This is a dictionary with the desired parameters
    :return:
    """
    df = copy.copy(dataframe)
    _rows_and_cols = []
    row_conditions = np.array([''])
    col_conditions = np.array([''])
    if rows_by is not None:
        _rows_and_cols.append(rows_by)
        row_conditions = df[rows_by].astype("category").cat.categories
        n_rows = row_conditions.size
    else:
        df.loc[:, 'dummy_row'] = ''
        _rows_and_cols.append('dummy_row')
        n_rows = 1
    idx_rows = np.arange(row_conditions.size)

    if cols_by is not None:
        _rows_and_cols.append(cols_by)
        col_conditions = df[cols_by].astype("category").cat.categories
        n_cols = col_conditions.size
    else:
        df.loc[:, 'dummy_col'] = ''
        _rows_and_cols.append('dummy_col')
        n_cols = 1
    idx_cols = np.arange(col_conditions.size)
    # check if input dataframe already contains the potentials. If not, then we extract them
    if 'potentials' in df.keys():
        if normalize:
            if normalize_by is not None:
                df = df.assign(
                    potentials=df.groupby(
                        normalize_by, observed=False)['potentials'].transform(
                        lambda x: x / np.ma.max(np.abs(np.ma.dstack([_val for _val in x])))))
            else:
                df = df.assign(
                    potentials=df.groupby(
                        [True] * len(df))['potentials'].transform(
                        lambda x: x / np.ma.max(np.abs(np.ma.dstack([_val for _val in x])))))
        sub_groups = df
    else:
        df['topo_value'] = df[topographic_value]
        if normalize:
            df = df.assign(
                topo_value=df.groupby(
                    [normalize_by], observed=False)[topographic_value].transform(lambda x: x / np.max(np.abs(x))))
        sub_groups = get_topographic_maps_as_df(dataframe=df,
                                                subject_id_column=subject_id_column,
                                                group_by=_rows_and_cols,
                                                channels_column='channel',
                                                topographic_value='topo_value',
                                                topographic_label=topographic_value,
                                                layout=layout,
                                                apply_function=apply_function,
                                                fun_args=fun_args,
                                                grid_size=grid_size,
                                                )
    if color_map_label is None:
        color_map_label = topographic_value
    groups = sub_groups.groupby(_rows_and_cols, observed=False)
    fig_out = plt.figure(constrained_layout=True)
    widths = [1.0] * n_cols
    heights = [1.0] * n_rows
    heights.append(0.1)  # this is for the color bar on the bottom
    heights.insert(0, 0.1)  # this is for the top labels
    widths.append(0.01)  # this is for the right labels
    gs = fig_out.add_gridspec(ncols=n_cols + 1, nrows=n_rows + 2,
                              width_ratios=widths,
                              height_ratios=heights,
                              )
    if max_topographic_value is None:
        max_sub_groups = sub_groups[sub_groups.potentials.apply(lambda x: np.size(x) > 1)]
        max_sub = max_sub_groups.potentials.apply(
            lambda x: np.ma.dstack([_val for _val in x]).max()).max()
    else:
        max_sub = max_topographic_value

    if min_topographic_value is None:
        min_sub_groups = sub_groups[sub_groups.potentials.apply(lambda x: np.size(x) > 1)]
        min_sub = min_sub_groups.potentials.apply(
            lambda x: np.ma.dstack([_val for _val in x]).min()).min()
    else:
        min_sub = min_topographic_value
    max_distance = sub_groups.max_distance.max()
    all_ax_row_label = []
    all_ax_col_label = []
    for _id, ((_current_row_group, _current_col_group), _group) in enumerate(groups):
        if _group.shape[0] == 0 or np.all(np.isnan(_group.potentials.values[0])):
            continue
        _idx_row = idx_rows[_current_row_group == row_conditions].squeeze() + 1
        _idx_col = idx_cols[_current_col_group == col_conditions].squeeze()
        ax = plt.subplot(gs[_idx_row, _idx_col])
        panel_title = ''
        if title_by == 'row':
            panel_title = '{:}'.format(_current_row_group)
        if title_by == 'col':
            panel_title = '{:}'.format(_current_col_group)

        if title_by == 'both':
            panel_title = '{:} / {:}'.format(_current_row_group, _current_col_group)

        ax.set_title(panel_title,
                     y=1 + title_v_offset,
                     size=fontsize,
                     fontweight='bold')
        if _group.potentials.values.size > 1:
            std_average = _group.potentials.apply(
                lambda x: apply_function(np.ma.dstack([_val for _val in x]), *fun_args)).values[0]
        else:
            std_average = _group.potentials.values[0]
        ax_im = ax.imshow(std_average.T, origin='lower',
                          extent=(-max_distance, max_distance, -max_distance, max_distance),
                          vmin=min_sub,
                          vmax=max_sub,
                          aspect=1.0)
        ax_im.set_cmap('nipy_spectral')

        levels = np.linspace(min_sub, max_sub, n_contour_levels)
        ax.contour(std_average.T,
                   levels,
                   origin='lower',
                   extent=(-max_distance, max_distance, -max_distance, max_distance),
                   linewidths=contour_line_width,
                   colors='k',
                   linestyles='solid')
        ax.autoscale(enable=False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.axis('off')
        # set right labels
        _last_col_ax = plt.subplot(gs[_idx_row, n_cols])
        _last_col_ax.set_xticks([])
        _last_col_ax.set_yticks([])
        _last_col_ax.axis('off')
        if not has_twin(_last_col_ax):
            ax_row_label = _last_col_ax.twinx()
            ax_row_label.autoscale(enable=False)
            ax_row_label.set_ylabel(_current_row_group,
                                    size=fontsize,
                                    rotation=-90)
            ax_row_label.set_yticklabels([])
            ax_row_label.tick_params(
                axis='y',  # changes apply to the y-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelleft=True,
                labelsize=fontsize)
            ax_row_label.spines['left'].set_visible(False)
            ax_row_label.spines['right'].set_visible(False)
            ax_row_label.spines['top'].set_visible(False)
            ax_row_label.spines['bottom'].set_visible(False)
            ax_row_label.set_xticks([])
            ax_row_label.set_yticks([])
            all_ax_row_label.append(ax_row_label)
        # set top labels
        _first_row_ax = plt.subplot(gs[0, _idx_col])
        _first_row_ax.set_xticks([])
        _first_row_ax.set_yticks([])
        _first_row_ax.axis('off')
        if not has_twin(_first_row_ax):
            ax_col_label = _first_row_ax.twiny()
            ax_col_label.autoscale(enable=False)
            ax_col_label.set_xlabel(_current_col_group, size=fontsize)
            ax_col_label.set_xticklabels([])
            ax_col_label.tick_params(
                axis='x',  # changes apply to the x-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelleft=True,
                labelsize=fontsize)
            ax_col_label.spines['left'].set_visible(False)
            ax_col_label.spines['right'].set_visible(False)
            ax_col_label.spines['top'].set_visible(False)
            ax_col_label.spines['bottom'].set_visible(False)
            ax_col_label.set_xticks([])
            ax_col_label.set_yticks([])
            all_ax_col_label.append(ax_col_label)
        # plot color bar
        if _id == 0:
            c_bar_ax = plt.subplot(gs[-1, :])
            c_bar = fig_out.colorbar(ax_im, cax=c_bar_ax, orientation='horizontal', format='%.1f')
            c_bar.set_label(color_map_label, fontsize=fontsize)
            tick_locator = ticker.MaxNLocator(nbins=3)
            c_bar.locator = tick_locator
            c_bar.update_ticks()
            c_bar.ax.tick_params(labelsize=fontsize)
        channels = _group.channels.values[0]
        channel_labels = [ch['label'] for ch in channels]
        ax.plot(0, max_distance * 1.0, '|', markersize=8, color='k')
        if show_sensors:
            _lay = Layout()
            _layout = _lay.get_layout(file_name=layout)
            _layout = np.array([_l for _l in _layout if _l.label not in ['COMNT', 'SCALE']])
            for i, lay in enumerate(_layout):
                if lay.label in channel_labels:
                    ax.plot(lay.x, lay.y, 'o', color='b', markersize=1)
                else:
                    ax.plot(lay.x, lay.y, 'o', color='grey', markersize=1)
                if show_sensor_label:
                    ax.text(lay.x, lay.y, s=lay.label, fontsize=6)

    all_axes = fig_out.get_axes()
    for ax in all_axes:
        if ax == c_bar.ax:
            continue
        ax.spines['top'].set_visible(False)
        # ax.set_xticklabels([])
        # ax.set_xlabel('')
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        # if title_by is not None and not ax.get_subplotspec().is_first_row():
        #     ax.set_title('')
    inch = 2.54
    fig_out.suptitle(title)
    fig_out.set_size_inches(3.2 * len(col_conditions) / inch, h=3.2 * len(row_conditions) / inch)
    return fig_out


def get_topographic_maps(df,
                         subject_id_column: str = 'subject_id',
                         channels_column: str = 'channel',
                         topographic_value: str | None = None,
                         layout: str | None = None,
                         grid_size: np.complex128 = 600j,
                         apply_function: object | None = None,
                         fun_args: dict = {}):
    _lay = Layout()
    _layout = _lay.get_layout(file_name=layout)
    _layout = np.array([_l for _l in _layout if _l.label not in ['COMNT', 'SCALE']])
    _single_responses = np.array([])

    df[subject_id_column] = df[subject_id_column].astype('category').cat.remove_unused_categories()
    _subject_groups = df.groupby(subject_id_column, observed=False, group_keys=False)
    for _, (_id_sub, _sub_group) in enumerate(_subject_groups):
        if _sub_group.size == 0:
            print('no data found for {:}'.format(_id_sub))
            continue
        if _sub_group.shape[0] < 4:
            print('no enough data points to generate topographic map ({:} points)'.format(_sub_group.shape[0]))
            continue
        x = []
        y = []
        z = []
        channels = []
        max_potential = -np.inf
        print('Using {:} data points to generate topographic map from layout with {:} sensors'.format(
            _sub_group.shape[0],
            _layout.size
        ))
        for _i, (_, _row) in enumerate(_sub_group.iterrows()):
            ch = _row[channels_column]
            amp = _row[topographic_value]
            for _l in _layout:
                if _l.label == ch:
                    x.append(_l.x)
                    y.append(_l.y)
                    z.append(amp)
            channels.append({'label': ch})

        _potentials, max_distance = eegpt.interpolate_potential_fields(x=np.array(x).reshape(-1, 1),
                                                                       y=np.array(y).reshape(-1, 1),
                                                                       z=np.array(z).reshape(-1, 1),
                                                                       grid=grid_size)
        max_potential
        if not _single_responses.size:
            _single_responses = _potentials[:, :, None]
        else:
            _single_responses = np.ma.dstack((_single_responses, _potentials))
    out = None
    if _single_responses.size:
        if apply_function is not None:
            _single_responses = apply_function(_single_responses, **fun_args)
        out = pd.Series(data={'potentials': _single_responses,
                              'max_distance': max_distance,
                              'channels': channels
                              })
    return out


def get_topographic_maps_as_df(dataframe: pd.DataFrame | None = None,
                               group_by: List[str] | None = None,
                               subject_id_column: str = 'subject_id',
                               channels_column: str = 'channel',
                               topographic_value: str | None = None,
                               topographic_label: str | None = None,
                               layout: str | None = None,
                               grid_size: np.complex128 = 600j,
                               apply_function: object = np.mean,
                               fun_args: dict = {'axis': 2}
                               ) -> pd.DataFrame:
    """
    This function will plot the waveforms contained in a pandas dataframe read using the sqlite_waveforms_to_pandas
    function of pEEGy.
    The rows and columns of the output plot are specified by the factors of the dataframe.
    The output will show the data for each of those factors (both individual and average data).
    :param dataframe: a pandas dataframe returned by sqlite_waveforms_to_pandas function of pEEGy.
    :param group_by: name of factors to group and obtain potentials.
    :param subject_id_column: string indicating the column name with subject ids
    :param channels_column: name of column containing channel labels
    :param topographic_value: name of column containing the value to be shown by the topographic map
    :param topographic_label: name of of the value to being mapped
    :param layout: path or name of the layout to be used
    :param grid_size: complex number indicating the size of the grid,
    :return:
    """
    df = copy.copy(dataframe)
    df['topo_value'] = df[topographic_value]
    if group_by is not None:
        for _g in group_by:
            df[_g] = df[_g].astype('category').cat.remove_unused_categories()
    else:
        group_by = [True] * len(df)
    sub_groups = df.groupby(group_by, group_keys=False, observed=True).apply(
        lambda x: get_topographic_maps(x,
                                       subject_id_column=subject_id_column,
                                       layout=layout,
                                       channels_column=channels_column,
                                       topographic_value='topo_value',
                                       grid_size=grid_size,
                                       apply_function=apply_function,
                                       fun_args=fun_args,
                                       ),
        include_groups=False).reset_index()
    sub_groups['topographic_label'] = topographic_label

    return sub_groups


def set_axis(ax: type(plt.axis) | None = None,
             _row: pd.DataFrame | None = None,
             _columns_legends: str | None = None,
             _y_unit_to: u.Unit | None = None,
             _x_unit_to: u.Unit | None = None,
             sub_average_time_buffer_size: int | None = None,
             # _last_col_ax: plt.Axes | None = None,
             _current_row_group: str | None = None,
             _current_col_group: str | None = None,
             _idx_row: int | None = None,
             _domain: str | None = None,
             time_xlim: [float, float] = None,
             time_ylim: [float, float] = None,
             freq_xlim: [float, float] = None,
             freq_ylim: [float, float] = None,
             time_vmarkers: type(np.array) | None = None,
             freq_vmarkers: type(np.array) | None = None,
             freq_vmarkers_style: str | None = None,
             show_individual_waveforms: bool = True,
             individual_waveforms_alpha: float = 0.1,
             show_mean: bool = True,
             show_sem: bool = False,
             sem_alpha: float = 0.2,
             show_sd: bool = True,
             sd_alpha: float = 0.2,
             show_legend: bool = True,
             title_by: str = 'row',
             title_v_offset: float = 0.0,
             fontsize: float = 6,
             color: [float, float, float] = None,
             _group_label: str | None = None,
             ):
    _group_label = []
    for _ic, _col in enumerate(_columns_legends):
        _group_label.append(str(_row[_col]))
    _group_label = '/'.join(_group_label)
    _domain = _row['domain']

    title = ''
    if title_by == 'row':
        title = '{:}'.format(_current_row_group)

    if title_by == 'col':
        title = '{:}'.format(_current_col_group)

    if title_by == 'both':
        title = '{:} / {:}'.format(_current_row_group, _current_col_group)

    if title_by == 'col':
        if _idx_row == 0:
            ax.set_title(title,
                         y=1 + title_v_offset,
                         size=fontsize,
                         fontweight='bold')
    else:
        ax.set_title(title,
                     y=1 + title_v_offset,
                     size=fontsize,
                     fontweight='bold')

    if show_individual_waveforms:
        ax.plot(_row['x'].value, _row['y_single_responses'].value,
                linewidth=0.5,
                alpha=individual_waveforms_alpha,
                color=color
                )
        if 'min_time' in _row.keys() and 'min_time_unit' in _row.keys():
            _peak_time = _row['min_time'] * u.Quantity(1, _row['min_time_unit']).to(_row['x'].unit)
            _idx_peak = np.argmin(np.abs(_row['x'] - _peak_time))
            ax.plot(_peak_time, _row['y_single_responses'][[_idx_peak], :],
                    markersize=3,
                    alpha=individual_waveforms_alpha,
                    color=color,
                    marker='v'
                    )
    if show_sem:
        ax.fill_between(_row['x'].value,
                        (_row['y_mean'] - _row['y_sem']).value * (_domain == Domain.time),
                        (_row['y_mean'] + _row['y_sem']).value,
                        alpha=sem_alpha,
                        edgecolor="none",
                        facecolor=color)
    if show_sd:
        ax.fill_between(_row['x'].value,
                        (_row['y_mean'] - _row['y_sd']).value * (_domain == Domain.time),
                        (_row['y_mean'] + _row['y_sd']).value,
                        alpha=sd_alpha,
                        edgecolor="none",
                        facecolor=color)
    if show_mean:
        ax.plot(_row['x'].value, _row['y_mean'].value,
                color=color,
                linewidth=0.8,
                label=_group_label)
        if 'min_time' in _row.keys() and 'min_time_unit' in _row.keys():
            _peak_time = _row['min_time'] * u.Quantity(1, _row['min_time_unit']).to(_row['x'].unit)
            _idx_peak = np.argmin(np.abs(_row['x'] - _peak_time))
            ax.plot(_peak_time.value, _row['y_mean'].value[_idx_peak],
                    markersize=3,
                    color=color,
                    marker='v'
                    )
        if 'max_time' in _row.keys() and 'max_time_unit' in _row.keys():
            _peak_time = _row['max_time'] * u.Quantity(1, _row['max_time_unit']).to(_row['x'].unit)
            _idx_peak = np.argmin(np.abs(_row['x'] - _peak_time))
            ax.plot(_peak_time.value, _row['y_mean'].value[_idx_peak],
                    markersize=3,
                    color=color,
                    marker='v'
                    )

    if _domain == Domain.time:
        if time_xlim is not None:
            ax.set_xlim(time_xlim)
        if time_ylim is not None:
            ax.set_ylim(time_ylim)
        if time_vmarkers is not None:
            [ax.axvline(_t, color='k', linestyle=':', linewidth=0.5) for _t in time_vmarkers]
        ax.set_xlabel('Time [{:}]'.format(_row['x'].unit), size=fontsize)

    if _domain == Domain.frequency:
        if freq_xlim is not None:
            ax.set_xlim(freq_xlim)
            if freq_ylim is None:
                _x_idx = np.where(np.logical_and(_row['x'].value >= np.min(freq_xlim),
                                                 _row['x'].value <= np.max(freq_xlim)))[0]
                _freq_ylim = [0, np.max(_row['y_mean'].value[_x_idx]) * 1.2]
                ax.set_ylim(_freq_ylim)

        if freq_ylim is not None:
            ax.set_ylim(freq_ylim)
        if freq_vmarkers is not None:
            if freq_vmarkers_style is None:
                [ax.axvline(_f, color='k', linestyle=':', linewidth=0.5) for _f in freq_vmarkers]
            else:
                y_min, y_max = ax.get_ylim()
                [ax.plot(_f, y_max * 0.93,
                         color='g',
                         marker=freq_vmarkers_style,
                         markersize=3) for _f in freq_vmarkers]
        ax.set_xlabel('Frequency [{:}]'.format(_row['x'].unit), size=fontsize)
    handles, labels = ax.get_legend_handles_labels()
    if len(labels) > 1 and show_legend:
        ax.legend(handles,
                  labels,
                  loc='upper center',
                  fontsize=fontsize,
                  frameon=False,
                  # ncol=len(labels)
                  )
    # return all_ax_row_label
    return


def add_waveforms_to_df(_row: pd.core.series.Series | None = None,
                        _y_unit_to: u.Unit | None = None,
                        _x_unit_to: u.Unit | None = None,
                        sub_average_time_buffer_size: int | None = None,
                        ):
    _series = _row.copy()
    y_unit = u.Quantity(1, _series['y_unit'])
    x_unit = u.Quantity(1, _series['x_unit'])
    if _y_unit_to is None:
        _y_unit_to = y_unit.unit
    if _x_unit_to is None:
        _x_unit_to = x_unit.unit
    y = (_series['y'] * y_unit).to(_y_unit_to)
    x = (_series['x'] * x_unit).to(_x_unit_to)
    fs = _series['x_fs']

    _domain = _series['domain']
    if y.ndim == 1:
        y = y.reshape([-1, 1])
    y_single_responses = y

    if _domain == Domain.time and sub_average_time_buffer_size is not None:
        fs = 1 / np.mean(np.diff(x))
        used_samples = int(np.floor(y.shape[0] // sub_average_time_buffer_size) * sub_average_time_buffer_size)
        y_f = y[0: used_samples, :]
        y_f = np.transpose(np.reshape(y_f, (sub_average_time_buffer_size, -1, y_f.shape[1]), order='F'),
                           [0, 2, 1])
        # demean
        y_f = np.mean(y_f, axis=2)
        x = np.arange(0, sub_average_time_buffer_size) / fs
        y_single_responses = y_f - np.mean(y_f, axis=0)
    y_mean = None
    y_sd = None
    y_sem = None
    if _domain == Domain.time:
        y_mean = np.mean(y_single_responses, axis=1)
        y_sd = np.std(y_single_responses, axis=1)
        y_sem = y_sd / np.sqrt(y_single_responses.shape[1])
    if _domain == Domain.frequency:
        y_mean = np.abs(np.mean(y_single_responses, axis=1))
        y_sd = np.std(np.abs(y_single_responses), axis=1)
        y_sem = y_sd / np.sqrt(y_single_responses.shape[1])
        y_single_responses = np.abs(y_single_responses)
    _series['y_single_responses'] = y_single_responses
    _series['y_mean'] = y_mean
    _series['y_sd'] = y_sd
    _series['y_sem'] = y_sem
    _series['x'] = x
    return _series


def get_insets(ax: plt.Axes):
    return [c for c in ax.get_children()
            if isinstance(c, plt.Axes)]


def get_all_topographic_maps(dataframe: pd.DataFrame | None = None,
                             channels_column: str = 'channel',
                             topographic_value: str | None = None,
                             layout: str | None = None,
                             group_by: List[str] = [],
                             grid_size: np.complex128 = 600j,
                             ) -> pd.DataFrame:
    df = dataframe.copy()
    df['topo_value'] = df[topographic_value]
    df['channel'] = df[channels_column]
    _group_by = ['subject_id',
                 'id_measurement',
                 'id_stimuli',
                 'id_recording'] + group_by
    # extract unique group values
    _group_by = list(sorted(set(_group_by).intersection(set(dataframe.columns)), key=lambda x: _group_by.index(x)))
    sub_groups = get_topographic_maps_as_df(
        dataframe=df,
        subject_id_column='id_subject',
        group_by=_group_by,
        channels_column='channel',
        topographic_value='topo_value',
        topographic_label=topographic_value,
        layout=layout,
        grid_size=grid_size,
    )
    # clean in case data could not be interpolated because of insufficient number of points
    sub_groups = pd.DataFrame.dropna(sub_groups, axis=0)
    sum_df = df.loc[df[_group_by].drop_duplicates().index]
    sum_df = sum_df.drop(columns=['topo_value', 'channel'])
    output = pd.concat([sum_df.set_index(_group_by),
                        sub_groups.set_index(_group_by)],
                       axis=1,
                       join='inner').reset_index()

    return output


def get_topographic_maps_group_by(dataframe: pd.DataFrame | None = None,
                                  group_by: List[str] | None = None,
                                  subject_id_column: str = 'subject_id',
                                  normalize_by: str = 'subject_id',
                                  channels_column: str = 'channel',
                                  topographic_value: str | None = None,
                                  layout: str | None = None,
                                  normalize: bool = False,
                                  apply_function: object = np.mean,
                                  fun_args: dict = {'axis': 2}
                                  ) -> pd.DataFrame:
    df = copy.copy(dataframe)
    # check if input dataframe already contains the potentials. If not, then we extract them
    df['topo_value'] = df[topographic_value]
    if normalize:
        df = df.assign(
            topo_value=df.groupby(
                [normalize_by], observed=False)[topographic_value].transform(lambda x: x / np.max(np.abs(x))))

    sub_groups = get_topographic_maps_as_df(dataframe=df,
                                            subject_id_column=subject_id_column,
                                            group_by=group_by,
                                            channels_column='channel',
                                            topographic_value='topo_value',
                                            topographic_label=topographic_value,
                                            layout=layout,
                                            apply_function=apply_function,
                                            fun_args=fun_args
                                            )
    return sub_groups


def group_topographic_df_by(dataframe: type(pd.DataFrame) | None = None,
                            group_by: List[str] | None = None):
    _subject_groups = dataframe.groupby(group_by, observed=False, group_keys=False)
    max_distance = -np.inf
    _unique_channels = []
    out_df = pd.DataFrame(columns=group_by + ['potentials', 'max_distance', 'channels', 'topographic_label'])
    for _, (_id_subgroup, _sub_group) in enumerate(_subject_groups):
        if _sub_group.size == 0:
            print('no data found for {:}'.format(_id_subgroup))
            continue
        _id_subgroup_str = [str(_val) for _val in _id_subgroup]
        print('topographic map group ' + '|'.join(_id_subgroup_str) + ': n = {:}'.format(_sub_group.shape[0]))
        _potentials = _sub_group['potentials']
        max_distance = np.maximum(max_distance, np.max(_sub_group['max_distance']))
        _single_responses = np.array([])
        for _p in _potentials:
            if not _single_responses.size:
                _single_responses = _p[:, :, None]
            else:
                _single_responses = np.ma.dstack((_single_responses, _p))
            if not len(_unique_channels):
                _unique_channels = set([_ch['label'] for _, _row in _sub_group['channels'].items() for _ch in _row])
            else:
                _unique_channels = set(_unique_channels).union(
                    set([_ch['label'] for _, _row in _sub_group['channels'].items() for _ch in _row]))

        _new_df = pd.DataFrame([list(_id_subgroup) + [_single_responses] + [None, None, None]],
                               columns=out_df.columns)
        if out_df.shape[0] == 0:
            out_df = _new_df
        else:
            out_df = pd.concat([_new_df, out_df], ignore_index=True)

    out_df['channels'] = out_df['channels'].apply(lambda x: [{'label': _value} for _value in _unique_channels])
    out_df['max_distance'] = max_distance
    out_df['topographic_label'] = '/'.join(dataframe['topographic_label'].unique())
    return out_df


def plot_time_frequency_responses_and_topographic_maps(dataframe: pd.DataFrame | None = None,
                                                       rows_by: str | None = None,
                                                       cols_by: str | None = None,
                                                       color_map: str = 'viridis',
                                                       sub_average_time_buffer_size: int | None = None,
                                                       time_xlim: type([float, float]) = None,
                                                       time_ylim: type([float, float]) = None,
                                                       freq_xlim: type([float, float]) = None,
                                                       freq_ylim: type([float, float]) = None,
                                                       time_vmarkers: type(np.array) | None = None,
                                                       freq_vmarkers: type(np.array) | None = None,
                                                       freq_vmarkers_style: str | None = None,
                                                       show_individual_waveforms: bool = True,
                                                       individual_waveforms_alpha: float = 0.1,
                                                       show_mean: bool = True,
                                                       show_sem: bool = False,
                                                       sem_alpha: float = 0.2,
                                                       show_sd: bool = True,
                                                       sd_alpha: float = 0.2,
                                                       show_legend: bool = True,
                                                       legend_location='upper center',
                                                       title_by: str = 'row',
                                                       title_v_offset: float = 0.0,
                                                       ylabel: str | None = None,
                                                       y_unit_to: u.Unit | None = None,
                                                       x_unit_to: u.Unit | None = None,
                                                       inset_y_unit_to: u.Unit | None = None,
                                                       inset_x_unit_to: u.Unit | None = None,
                                                       fontsize: float = 6,
                                                       group_by: list[str] | None = None,
                                                       colour_by: list[str] | None = None,
                                                       show_column_labels: bool = True,
                                                       insets_position: type([float, float, float, float]) = None,
                                                       color_map_label: str | None = None,
                                                       colormap_size: float = 0.1,
                                                       normalize: bool = False,
                                                       show_sensors: bool = True,
                                                       show_sensor_label: bool = False,
                                                       n_contour_levels: int = 35,
                                                       max_topographic_value: float | None = None,
                                                       min_topographic_value: float | None = None,
                                                       commom_topographic_value: bool = True,
                                                       contour_line_width: float = 0.1,
                                                       apply_function: object = np.nanmean,
                                                       fun_args: dict = {'axis': 2},
                                                       topographic_maps_direction: str = 'v',
                                                       inset_scale: float = 1,
                                                       ) -> plt.figure:
    """
    This function will plot the waveforms contained in a pandas dataframe read using the sqlite_waveforms_to_pandas
    function of pEEGy.
    The rows and columns of the output plot are specified by the factors of the dataframe.
    The output will show the data for each of those factors (both individual and average data).
    :param dataframe: a pandas dataframe returned by sqlite_waveforms_to_pandas function of pEEGy
    :param rows_by: name of the factor in the dataframe for which the rows in the plot will be split
    :param cols_by: name of the factor in the dataframe for which the columns in the plot will be split
    :param color_map: name of matplotlib colormap (e.g. 'viridis', 'Spectral', 'coolwarm', etcetera
    :param sub_average_time_buffer_size: This is a parameter used to sub_average time_domain data. For example, if each
    of your data have 10000 points, and you want to show the average having a length of 1000 samples, you could specify
    sub_average_time_buffer_size = 1000. This will averaged the 10000 points by splitting the data into blocks of 1000
    samples
    :param time_xlim: x axis limit for the time-domain panels
    :param time_ylim: y axis limit for the time-domain panels
    :param freq_xlim: x axis limit for the frequency-domain panels
    :param freq_ylim: y axis limit for the frequency-domain panels
    :param time_vmarkers: array with x values to add a vertical marker in the time-domain panels
    :param freq_vmarkers: array with x values to add a vertical marker in the frequency-domain panels
    :param show_individual_waveforms: if true, individual waveforms will be shown.
    :param individual_waveforms_alpha: value between 0 and 1 indicating the alpha level of individual waveforms
    :param show_mean: if true, the mean across conditions will be shown
    :param show_sem: if true, the standard error of the mean will be shown
    :param sem_alpha: value between 0 and 1 indicating the alpha level of the sem
    :param show_sd: if true, the standard deviation of the mean will be shown
    :param sd_alpha: value between 0 and 1 indicating the alpha level of the standard deviation
    :param show_legend: if True, the legend for any other category present in the dataframe will be shown
    :param title_by: string specifying from which factor you want to show the titles in each panel. This can be: "row",
    "col", or "both"
    :param title_v_offset: float specifying the vertical offset of the title
    :param freq_vmarkers_style: style of the marker in the frequency-domain. If not passed, vertical lines are used.
    :param ylabel: Label to put in the vertical axis. If empty, the Amplitude and unit of it are used.
    :param y_unit_to: Specify the units in which the vertical axis will be displayed
    :param x_unit_to: Specify the units in which the horizontal axis will be displayed
    :param fontsize: the font size
    :param group_by: list of keys in dataframe which will be grouped. If colour_by is None, then colour is determined by
     group_by
    :param colour_by: list of keys in dataframe used to generate colours codes for the figure.
    :param show_column_labels: bool indicatint whether the columns labels should be shown
    :param color_map_label: string with the label that would be use of the colourmap. If empty, the default value will
    be the topographic_value
    :param topographic_maps_direction: direction ('v' or 'h') of topographic maps within each panel.
    :param normalize: if True, topographic maps will be normalized within normalize_by
    :param show_sensors: if True, the position of the sensors will be shown
    :param show_sensor_label: if True, the label of the sensor will be shown
    :param n_contour_levels: number of contour lines to plot
    :param min_topographic_value: if given, the colour scale will be restricted to have this value as maximum, otherwise
    it will be determined from the data.
    :param max_topographic_value: if given, the colour scale will be restricted to have this value as minimum, otherwise
    it will be determined from the data.
    :param contour_line_width: float indicating the with (in points) of the contour lines
    :param apply_function: function to be applied to each subgroup
    :return:
    """
    df = copy.copy(dataframe)
    df.reset_index(inplace=True, drop=True)
    _rows_and_cols = []
    row_conditions = np.array([''])
    col_conditions = np.array([''])
    if 'domain' not in df.keys():
        df['domain'] = Domain.time
        print('domain not defined in dataframe, assuming {:} domain'.format(Domain.time))
    if rows_by is not None:
        _rows_and_cols.append(rows_by)
        row_conditions = df[rows_by].astype("category").cat.categories
        row_domains = df.iloc[df[rows_by].index]['domain'].unique()
        unique_row_domains = row_domains.size == 1
        n_rows = row_conditions.size
    else:
        df.loc[:, 'dummy_row'] = ''
        _rows_and_cols.append('dummy_row')
        row_domains = df['domain'].unique()
        unique_row_domains = row_domains.size == 1
        n_rows = 1
    idx_rows = np.arange(row_conditions.size)
    if cols_by is not None:
        _rows_and_cols.append(cols_by)
        col_conditions = df[cols_by].astype("category").cat.categories
        n_cols = col_conditions.size
    else:
        df.loc[:, 'dummy_col'] = ''
        _rows_and_cols.append('dummy_col')
        n_cols = 1
    idx_cols = np.arange(col_conditions.size)
    _x_unit_to = x_unit_to
    _y_unit_to = y_unit_to
    # set colurs from colormap
    df['dummy_color_categories'] = ''
    iterate_by = None
    new_var = pd.Series(df.loc[:, ['dummy_color_categories']].values[:, 0])
    if group_by is None and colour_by is None:
        n_colors = 1
        unique_color_factors = np.array([''])
    else:
        iterate_by = group_by
        if colour_by is not None:
            iterate_by = colour_by
        for _col_name in iterate_by:
            new_var = new_var + df[_col_name].values.astype(str)
        df['dummy_color_categories'] = new_var
        for _col_name in iterate_by:
            df[_col_name] = pd.Categorical(df[_col_name])
        # sort to keep factor order in colours
        df.sort_values(by=iterate_by, inplace=True)
        vals, idx = np.unique(df['dummy_color_categories'], return_index=True)
        unsorted_unique = vals[np.argsort(idx)]

        df['dummy_color_categories'] = pd.Categorical(df['dummy_color_categories'],
                                                      categories=unsorted_unique)
        unique_color_factors = np.array(df['dummy_color_categories'].cat.categories.tolist())

    n_colors = unique_color_factors.size
    cmap = mpl.colormaps[color_map]
    _colors = cmap(np.linspace(0, 1, n_colors))
    _colors = [mpl.colors.to_hex(cmap(i)) for i in range(n_colors)]
    groups = df.groupby(_rows_and_cols, observed=False, sort=True)
    fig_out = plt.figure(constrained_layout=False)
    # set up subplots
    widths = [1.0] * n_cols
    heights = [1.0] * n_rows
    heights.insert(0, 0.01)  # this is for the top labels
    widths.append(0.01)  # this is for the right labels
    gs = fig_out.add_gridspec(ncols=n_cols + 1, nrows=n_rows + 1,
                              width_ratios=widths,
                              height_ratios=heights,
                              )

    all_ax_row_label = []
    all_ax_col_label = []
    # attach all axis to figure to ensure the are all created before calling them
    [plt.subplot(gs[_idx_row, _idx_col]) for _idx_row in range(gs.get_geometry()[0]) for _idx_col in
     range(gs.get_geometry()[1])]
    inset_axes = []

    if commom_topographic_value and max_topographic_value is None:
        _df = df.dropna(axis=0)
        max_topographic_value = _df.potentials.apply(lambda x: np.max(
            apply_function(x, **fun_args))).max()
    if commom_topographic_value and min_topographic_value is None:
        min_topographic_value = _df.potentials.apply(lambda x: np.min(
            apply_function(x, **fun_args))).min()
    has_colormap = False
    for _id, ((_current_row_group, _current_col_group), _group) in enumerate(groups):
        _current_group = _group
        if iterate_by is not None:
            _current_group.sort_values(by=iterate_by, inplace=True)
        _idx_row = idx_rows[_current_row_group == row_conditions].squeeze() + 1
        _idx_col = idx_cols[_current_col_group == col_conditions].squeeze()
        ax = plt.subplot(gs[_idx_row, _idx_col])
        _last_col_ax = plt.subplot(gs[_idx_row, n_cols])
        _columns_legends = []
        for _col in _current_group:
            _filter = _current_group[_col].apply(lambda x:
                                                 not (isinstance(x, str) or
                                                      isinstance(x, float) or
                                                      isinstance(x, int)))
            if np.any(_filter.values):
                continue
            if colour_by is not None:
                if _col in colour_by:
                    _columns_legends.append(_col)
            else:
                if group_by is not None:
                    if _col in group_by:
                        _columns_legends.append(_col)
                elif len(_current_group[_col].unique()) > 1:
                    _columns_legends.append(_col)
        for _i, (_, _row) in enumerate(_current_group.iterrows()):
            # get color index
            _color_index, = np.where(_row['dummy_color_categories'] == unique_color_factors)
            _color_index = int(_color_index)
            _row_summary = add_waveforms_to_df(
                _row=_row,
                _y_unit_to=y_unit_to,
                _x_unit_to=x_unit_to,
                sub_average_time_buffer_size=sub_average_time_buffer_size
            )
            set_axis(ax=ax,
                     _row=_row_summary,
                     _columns_legends=_columns_legends,
                     _current_row_group=_current_row_group,
                     _current_col_group=_current_col_group,
                     _idx_row=_idx_row,
                     time_xlim=time_xlim,
                     time_ylim=time_ylim,
                     freq_xlim=freq_xlim,
                     freq_ylim=freq_ylim,
                     time_vmarkers=time_vmarkers,
                     freq_vmarkers=freq_vmarkers,
                     freq_vmarkers_style=freq_vmarkers_style,
                     show_individual_waveforms=show_individual_waveforms,
                     individual_waveforms_alpha=individual_waveforms_alpha,
                     show_mean=show_mean,
                     show_sem=show_sem,
                     sem_alpha=sem_alpha,
                     show_sd=show_sd,
                     sd_alpha=sd_alpha,
                     show_legend=show_legend,
                     title_by=title_by,
                     title_v_offset=title_v_offset,
                     fontsize=fontsize,
                     color=_colors[_color_index],
                     )
        # all_ax_row_label.append(_last_col_ax)
        # set right labels
        _last_col_ax.set_xticks([])
        _last_col_ax.set_yticks([])
        _last_col_ax.axis('off')
        if not has_twin(_last_col_ax):
            ax_row_label = _last_col_ax.twinx()
            ax_row_label.autoscale(enable=False)
            ax_row_label.set_ylabel(_current_row_group,
                                    size=fontsize,
                                    rotation=-90,
                                    fontweight='bold')
            ax_row_label.set_yticklabels([])
            ax_row_label.tick_params(
                axis='y',  # changes apply to the y-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelright=True,
                labelsize=fontsize)
            ax_row_label.spines['left'].set_visible(False)
            ax_row_label.spines['right'].set_visible(False)
            ax_row_label.spines['top'].set_visible(False)
            ax_row_label.spines['bottom'].set_visible(False)
            ax_row_label.set_xticks([])
            ax_row_label.set_yticks([])
            all_ax_row_label.append(ax_row_label)
        # set top labels
        _first_row_ax = plt.subplot(gs[0, _idx_col])
        _first_row_ax.set_xticks([])
        _first_row_ax.set_yticks([])
        _first_row_ax.axis('off')
        if not has_twin(_first_row_ax):
            ax_col_label = _first_row_ax.twiny()
            ax_col_label.autoscale(enable=False)
            if show_column_labels:
                ax_col_label.set_xlabel(_current_col_group,
                                        size=fontsize,
                                        fontweight='bold')
            ax_col_label.set_xticklabels([])
            ax_col_label.tick_params(
                axis='x',  # changes apply to the x-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=False,  # ticks along the top edge are off
                labelleft=True,
                labelsize=fontsize)
            ax_col_label.spines['left'].set_visible(False)
            ax_col_label.spines['right'].set_visible(False)
            ax_col_label.spines['top'].set_visible(False)
            ax_col_label.spines['bottom'].set_visible(False)
            ax_col_label.set_xticks([])
            ax_col_label.set_yticks([])
            all_ax_col_label.append(ax_col_label)

        # plot topographic map
        _current_group = _current_group.dropna(axis=0)
        if _current_group.shape[0] > 0:
            _current_group = _current_group.drop(_rows_and_cols,
                                                 axis=1)
            show_colormap = not (commom_topographic_value and has_colormap)
            _inset_axes = inset_topographic_map(dataframe=_current_group,
                                                ax=ax,
                                                insets_position=insets_position,
                                                direction=topographic_maps_direction,
                                                vmin=min_topographic_value,
                                                vmax=max_topographic_value,
                                                contour_line_width=contour_line_width,
                                                n_contour_levels=n_contour_levels,
                                                scale=inset_scale,
                                                fontsize=fontsize,
                                                show_colormap=show_colormap,
                                                colormap_size=colormap_size,
                                                group_label=group_by
                                                )
            inset_axes = inset_axes + _inset_axes
            has_colormap = True

            if _x_unit_to is None:
                _x_unit_to = _row_summary['x_unit']
            if _y_unit_to is None:
                _y_unit_to = _row_summary['y_unit']
    all_axes = fig_out.get_axes()
    all_axes = list(set(all_axes) - set(inset_axes))
    axis_with_data = [ax for ax in all_axes if
                      ax not in all_ax_row_label and
                      ax not in all_ax_col_label and
                      ax.has_data()]
    all_axis_with_data = np.all(axis_with_data)
    # check if there is a common legend. If so, then we keep only one across all axes
    _unique_labels = []
    _unique_handles = []
    for _ax in axis_with_data:
        _handles, _labels = _ax.get_legend_handles_labels()
        if len(_handles) > 0 and len(_labels) > 0:
            _unique_handles = _unique_handles + [_handles]
            _unique_labels = _unique_labels + [_labels]
    common_labels = True
    for _idx_ul in range(len(_unique_labels) - 1):
        diff = set(_unique_labels[_idx_ul]) - set(_unique_labels[_idx_ul + 1])
        if len(diff) > 0:
            common_labels = False
            break
    if common_labels and len(_unique_handles) > 0:
        for _ax in axis_with_data:
            if _ax.legend_ is not None:
                _ax.get_legend().remove()
        _the_labels = _unique_labels[0]
        _the_handles = np.array(_unique_handles[0])
        # keep unique colour catctors
        _, _indices = np.unique(_the_labels, return_index=True)
        _the_labels = [_the_labels[_i] for _i in _indices]
        _the_handles = [_the_handles[_i] for _i in _indices]
        fig_out.legend(_the_handles,
                       _the_labels,
                       loc=legend_location,
                       fontsize=fontsize,
                       frameon=False,
                       ncol=len(_unique_labels[0]),
                       handlelength=1
                       )

    if ylabel is None:
        if _y_unit_to is not None:
            fig_out.supylabel('Amplitude [{:}]'.format(_y_unit_to), size=fontsize)
    else:
        fig_out.supylabel(ylabel, size=fontsize)
    if unique_row_domains and all_axis_with_data and np.all(row_domains == 'time') and n_cols > 1:
        fig_out.supxlabel('Time [{:}]'.format(_x_unit_to), size=fontsize)
    if unique_row_domains and all_axis_with_data and np.all(row_domains == 'frequency') and n_cols > 1:
        fig_out.supxlabel('Frequency [{:}]'.format(_x_unit_to), size=fontsize)

    unique_x_lim_per_row = []
    for _i_col in range(gs.get_geometry()[1] - 1):
        all_axis = [plt.subplot(gs[_i_row, _i_col]) for _i_row in range(1, gs.get_geometry()[0])]
        lims = []
        for _ax in all_axis:
            lims.append(np.array(_ax.get_xlim()))
        unique_x_lim_per_row.append(np.unique(np.array(lims), axis=0).shape[0] == 1)
    unique_x_lim = np.all(unique_x_lim_per_row)

    unique_y_lim_per_col = []
    for _i_row in range(1, gs.get_geometry()[0]):
        all_axis = [plt.subplot(gs[_i_row, _i_col]) for _i_col in range(gs.get_geometry()[1] - 1)]
        lims = []
        for _ax in all_axis:
            lims.append(np.array(_ax.get_ylim()))
        unique_y_lim_per_col.append(np.unique(np.array(lims), axis=0).shape[0] == 1)
    unique_y_lim = np.all(unique_y_lim_per_col)
    for ax in all_axes:
        if not ax.has_data() and ax not in all_ax_row_label and ax not in all_ax_col_label:
            ax.set_visible(False)
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set_xlabel('')
            continue
        ax.spines['top'].set_visible(False)
        if ax not in all_ax_col_label:
            if unique_row_domains and all_axis_with_data:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_last_row() and ax.has_data():
                    ax.set_xticklabels([])
                    ax.set_xlabel('')
                if n_cols > 1:
                    ax.set_xlabel('')
            elif unique_x_lim:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_last_row() and ax.has_data():
                    ax.set_xticklabels([])
                    ax.set_xlabel('')

            if unique_y_lim:
                subplotspec = ax.get_subplotspec()
                if subplotspec is not None and not subplotspec.is_first_col() and ax.has_data():
                    ax.set_yticklabels([])
                    ax.set_ylabel('')

        # ax.spines['left'].set_visible(True)
        ax.spines['right'].set_visible(False)
        ax.tick_params(labelsize=fontsize)

    inch = 2.54
    fig_out.set_size_inches(12.0 / inch, 2.25 * len(row_conditions) / inch)
    fig_out.subplots_adjust(top=0.98, bottom=0.08, hspace=0.0, left=0.15, right=0.95)
    # fig_out.tight_layout()
    return fig_out


def inset_topographic_map(dataframe: pd.DataFrame | None = None,
                          ax: object = None,
                          insets_position: type(list[float, float, float, float]) = None,
                          apply_function: object | None = np.mean,
                          fun_args: {} = {'axis': 2},
                          direction: str = 'v',
                          vmin: float | None = None,
                          vmax: float | None = None,
                          contour_line_width: float = 0.1,
                          n_contour_levels: int = 35,
                          fontsize: float = 8,
                          scale: float = 1,
                          show_colormap: bool = True,
                          colormap_size: float = 0.1,
                          group_label: List[str] | None = None,
                          ):
    df = dataframe.copy().reset_index(drop=True)
    if 'dummy_color_categories' in df.keys():
        df = df.drop(['dummy_color_categories'], axis=1)
    topo_label = '/'.join(df['topographic_label'].unique())

    grouping_variables = list(set(df.keys()) - set(['x',
                                                    'y',
                                                    'x_fs',
                                                    'x_unit',
                                                    'y_unit',
                                                    'potentials',
                                                    'max_distance',
                                                    'channels']))
    current_identifier = []
    for col in grouping_variables:
        df[col] = df[col].astype('category')
        if df[col].cat.categories.size > 1:
            current_identifier = current_identifier + [col]
    if group_label is not None:
        current_identifier = [item for item in current_identifier if item in group_label]
    n_topographic_maps = df.shape[0]
    if apply_function is not None:
        df['potentials'] = df['potentials'].apply(lambda x: apply_function(x, **fun_args))

    if vmin is None:
        min_sub_groups = df[df.potentials.apply(lambda x: np.size(x) > 1)]
        min_sub = min_sub_groups.potentials.apply(
            lambda x: np.min(x)).min()
    else:
        min_sub = vmin
    if vmax is None:
        max_sub_groups = df[df.potentials.apply(lambda x: np.size(x) > 1)]
        max_sub = max_sub_groups.potentials.apply(
            lambda x: np.max(x)).max()
    else:
        max_sub = vmax

    levels = np.linspace(min_sub, max_sub, n_contour_levels)

    _position = insets_position
    if direction not in ['v', 'h']:
        print('unknown direction {:}. using "v"'.format(direction))
        direction = 'v'

    if insets_position is None:
        height = scale * 0.5 / n_topographic_maps
        width = scale * 0.5 / n_topographic_maps
        if direction == 'v':
            _position = [1 - width,
                         0.25,
                         width,
                         0.5 / n_topographic_maps]
            _colormap_position = [1 - width * 1.1,
                                  0.25,
                                  width * colormap_size,
                                  0.5
                                  ]
        else:
            _position = [0.25,
                         1 - height,
                         0.5 / n_topographic_maps,
                         height]
            _colormap_position = [0.25,
                                  1 - height * 1.1,
                                  0.5,
                                  height * colormap_size
                                  ]
    else:
        if direction == 'v':
            width = scale * _position[2]
            height = scale * _position[3] / n_topographic_maps
            _position = [_position[0], _position[1], width, height]
            _colormap_position = [_position[0] * 0.9,
                                  _position[1],
                                  width * colormap_size,
                                  height * n_topographic_maps]
        else:
            width = scale * _position[2] / n_topographic_maps
            height = scale * _position[3]
            _position = [_position[0], _position[1], width, height]
            _colormap_position = [_position[0],
                                  _position[1] * 0.975,
                                  width * n_topographic_maps,
                                  height * colormap_size]

    _position = tuple(_position)
    all_insets = []
    ax_im = None
    for _i, _row in df.iterrows():
        if direction == 'v':
            _current_position = np.array(_position) + np.array([0, height * _i, 0, 0])
        else:
            _current_position = np.array(_position) + np.array([width * _i, 0, 0, 0])
        _current_topomap = _row['potentials']
        max_distance = _row['max_distance']
        inset_ax = ax.inset_axes(_current_position,
                                 transform=ax.transAxes)

        ax_im = inset_ax.imshow(_current_topomap.T,
                                origin='lower',
                                extent=(-max_distance, max_distance, -max_distance, max_distance),
                                vmin=min_sub,
                                vmax=max_sub,
                                aspect=1.0)
        ax_im.set_cmap('nipy_spectral')

        inset_ax.contour(_current_topomap.T,
                         levels,
                         origin='lower',
                         extent=(-max_distance, max_distance, -max_distance, max_distance),
                         linewidths=contour_line_width,
                         colors='k',
                         linestyles='solid')
        inset_ax.autoscale(enable=False)
        inset_ax.set_xticks([])
        inset_ax.set_yticks([])
        inset_ax.axis('off')
        if len(current_identifier) > 0:
            label = '/'.join([str(_row[_col]) for _col in current_identifier])
            if direction == 'v':
                ax_row_label = inset_ax.twinx()
                ax_row_label.autoscale(enable=False)
                ax_row_label.set_yticklabels([])
                ax_row_label.tick_params(
                    axis='y',  # changes apply to the y-axis
                    which='both',  # both major and minor ticks are affected
                    right=False,  # ticks along the bottom edge are off
                    left=False,  # ticks along the top edge are off
                    labelright=True,
                    labelsize=fontsize)
                ax_row_label.spines['left'].set_visible(False)
                ax_row_label.spines['right'].set_visible(False)
                ax_row_label.spines['top'].set_visible(False)
                ax_row_label.spines['bottom'].set_visible(False)
                ax_row_label.set_xticks([])
                ax_row_label.set_yticks([])
                ax_row_label.set_ylabel(label,
                                        size=fontsize,
                                        rotation=-90)
                all_insets.append(ax_row_label)
            else:
                ax_row_label = inset_ax.twiny()
                ax_row_label.autoscale(enable=False)
                ax_row_label.set_yticklabels([])
                ax_row_label.tick_params(
                    axis='x',  # changes apply to the y-axis
                    which='both',  # both major and minor ticks are affected
                    top=False,  # ticks along the bottom edge are off
                    bottom=False,  # ticks along the top edge are off
                    labelbottom=True,
                    labelsize=fontsize)
                ax_row_label.spines['left'].set_visible(False)
                ax_row_label.spines['right'].set_visible(False)
                ax_row_label.spines['top'].set_visible(False)
                ax_row_label.spines['bottom'].set_visible(False)
                ax_row_label.set_xticks([])
                ax_row_label.set_yticks([])
                ax_row_label.set_xlabel(label, size=fontsize)
                all_insets.append(ax_row_label)
    if show_colormap:
        if direction == 'v':
            ax_colormap = ax.inset_axes(_colormap_position,
                                        transform=ax.transAxes)
            c_bar = ax.figure.colorbar(ax_im,
                                       cax=ax_colormap,
                                       orientation='vertical',
                                       format='%.1f')
            c_bar.ax.tick_params(
                axis='y',  # changes apply to the y-axis
                which='both',  # both major and minor ticks are affected
                right=False,  # ticks along the bottom edge are off
                left=True,  # ticks along the top edge are off
                labelleft=True,
                labelright=False,
                labelsize=fontsize,
                # size=fontsize
            )
            c_bar.set_label(topo_label, fontsize=fontsize)
        else:
            ax_colormap = ax.inset_axes(_colormap_position,
                                        transform=ax.transAxes)
            c_bar = ax.figure.colorbar(ax_im,
                                       cax=ax_colormap,
                                       orientation='horizontal',
                                       format='%.1f')
            c_bar.ax.tick_params(
                axis='x',  # changes apply to the y-axis
                which='both',  # both major and minor ticks are affected
                labelsize=fontsize,
                # size=fontsize
            )
            c_bar.set_label(topo_label, fontsize=fontsize)

        tick_locator = ticker.MaxNLocator(nbins=3)
        c_bar.locator = tick_locator
        c_bar.update_ticks()
        all_insets.append(ax_colormap)
    return all_insets


def get_waveforms_and_topographic_maps_df(
        database_path: str = None,
        channels: List[str] = None,
        group_by: List[str] = None,
        data_source_waveforms: List[str] = None,
        data_source_topographic_maps: List[str] = None,
        data_source_stat_table: str = 'f_test',
        topographic_value: str = 'f',
        layout: str = 'biosemi64_2_EXT.lay',
        prepare_dataframe: object = None,
        user_query_waveforms: str | None = None,
        user_query_topographic_maps: str | None = None,
        grid_size: np.complex128 = 600j,
        filters: str | None = None
):
    """
    This function will generate a dataframe with waveforms and topographic maps that can be directly used with
    plot_time_frequency_responses_and_topographic_maps to generate figures.
    :param database_path: str pointing to the database
    :param channels: list of channels to extract waveforms
    :param group_by: list grouping keys in dataframe
    :param data_source_waveforms: list of data_source(s) (within the waveforms table in the database) to extract
    waveforms
    :param data_source_topographic_maps: list of data_source(s) (within the data_source_stat_table table in the
    database) to extract the topographic value to be shown
    :param data_source_stat_table: str pointing to the data_source_stat_table in the database us to extract the
    topographic_value
    :param topographic_value: column within the selected table (data_source_stat_table) to be shown
    :param layout: the EEG layout used to plot the topographic map
    :param prepare_dataframe: arbitrary function new_df <- function(df) used to modify the dataframes as desired
    :param user_query_waveforms: This parameter can be used to include or exclude waveforms data based on a logical
    condition, e.g. 'subject_id != "S1"'
    :param user_query_topographic_maps: This parameter can be used to include or exclude data in the topographic maps
     based on a logical condition, e.g. 'subject_id != "S1"'
    :param grid_size: resolution of the topographic maps
    :param filters: pandas query string applied after the prepare_dataframe function has finished.
    This query will be applied to both waveforms and topographic maps dataframes
    :return: pandas dataframe with waveforms and topographic maps that can be used directly with
    plot_time_frequency_responses_and_topographic_maps to generate figures
    """

    df = sqlite_all_waveforms_to_pandas(database_path=database_path,
                                        channels=channels,
                                        user_query=user_query_waveforms
                                        )
    if prepare_dataframe is not None:
        df = prepare_dataframe(df)

    if filters is not None:
        df = df.query(filters)
    df_waveforms_grouped = group_waveforms_df_by(df,
                                                 group_by=group_by)
    df_waveforms_grouped = df_waveforms_grouped[(df_waveforms_grouped['data_source'].isin(data_source_waveforms))]
    df_topo_maps = sqlite_tables_to_pandas(database_path=database_path,
                                           tables=[data_source_stat_table],
                                           user_query=user_query_topographic_maps)[data_source_stat_table]
    if prepare_dataframe is not None:
        df_topo_maps = prepare_dataframe(df_topo_maps)

    df_topo_maps = df_topo_maps[(df_topo_maps['data_source'].isin(data_source_topographic_maps))]

    if filters is not None:
        df_topo_maps = df_topo_maps.query(filters)

    df_topo = get_all_topographic_maps(dataframe=df_topo_maps,
                                       channels_column='channel',
                                       topographic_value=topographic_value,
                                       layout=layout,
                                       group_by=group_by,
                                       grid_size=grid_size
                                       )
    df_topo_grouped = group_topographic_df_by(df_topo, group_by=group_by)
    df_waveforms_grouped['data_source'] = ''
    df_topo_grouped['data_source'] = ''
    df_out = pd.concat([df_waveforms_grouped.set_index(group_by),
                        df_topo_grouped.set_index(group_by)],
                       axis=1,
                       join='inner').reset_index()

    return df_out
