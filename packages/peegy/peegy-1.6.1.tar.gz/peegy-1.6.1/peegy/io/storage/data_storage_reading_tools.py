import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype
from peegy.definitions.channel_definitions import Domain
from peegy.processing.pipe.storage import SubjectInformation, MeasurementInformation
import sqlite3
from scipy.interpolate import interp1d
import io
import astropy.units as u
from typing import List
import pathlib
import os
__author__ = 'jundurraga-ucl'


class PandasDataPages(dict):
    """This class manages pandas dataframes appended to it.
    When data frames are appended the PandasDataPages specific dataframe can be called by its name
    """

    def __init__(self):
        super(PandasDataPages, self).__init__()

    def __setitem__(self, name, dataframe: pd.DataFrame | None = None):
        # optional processing here
        assert isinstance(dataframe, pd.DataFrame)
        name = self.ensure_unique_name(label=name)
        super(PandasDataPages, self).__setitem__(name, dataframe)
        # we add the new item as class variable
        setattr(self, name, dataframe)

    def append(self, item: object, name=None):
        if name is None:
            name = type(item).__name__
        self[name] = item

    def ensure_unique_name(self, label: str | None = None):
        all_names = [_key for _key in self.keys()]
        _label = label
        count = 0
        while _label in all_names:
            _label = label + '_' + str(count)
            count = count + 1
        if count > 0:
            print('PandasDataPages item "{:}" already exists. Renamed to "{:}"'.format(label, _label))
        return _label

    def __getitem__(self, key):
        return super(PandasDataPages, self).__getitem__(key)


def sqlite_tables_to_pandas(database_path: str | None = None,
                            tables: List[str] | None = None,
                            user_query: str | None = None,
                            subject_information: SubjectInformation = None,
                            measurement_information: MeasurementInformation = None) -> pd.DataFrame:
    """
    This function will return a pandas dataframe containing the desired tables from a pEEGy .sqlite database.
    A pEEGy database will always contain a table 'subjects', 'measurement_info' , 'stimuli', 'recording'.
    Each subject will be linked to measurement by their id. Similarly, each measurement will be linked to each stimulus
    by its id.
    Any other table, for example, recording, waveforms, hotelling_t2_time, hotelling_t2_freq, f_test_time, f_test_freq,
    or other tables created by the user, will be uniquely related to each subject, measurement, recording, and stimuli
    by id_subject, id_measurement, id_recording, and _id_stimuli, respectively.
    This function will provide a user-friendly pandas dataframe by pooling together this information by indexing the
    corresponding ids to their respective values.
    :param database_path: path to the database from which we will read the tables
    :param tables: a list of strings containing the tables want to read. Make sure these tables are present in the
    database
    :param user_query: list with user queries to filter the data
    :param subject_information: SubjectInformation class. If provided, then the query will filter cases matching the
    information contained in this class
    :param measurement_information: MeasurementInformation class. If provided, then the query will filter cases matching
    the information contained in this class
    :return: a pandas dataframe with the respective tables.
    """
    out = PandasDataPages()
    db = sqlite3.connect(database_path)
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [_tables[0] for _tables in cursor.fetchall()]
    extra_tables = ''
    extra_outputs = ''
    extra_join = ''
    subject_filter = []
    subject_filter_query = ''
    measurement_filter = []
    measurement_filter_query = ''
    if subject_information is not None:
        for name, value in subject_information.__dict__.items():
            if name == 'group':
                name = '"group"'
            if isinstance(value, str):
                subject_filter.append('(SUB.{:} IS NULL OR SUB.{:} = "{:}") '.format(name,
                                                                                     name,
                                                                                     value))
            if isinstance(value, float):
                subject_filter.append('(SUB.{:} IS NULL OR SUB.{:} = {:}) '.format(name,
                                                                                   name,
                                                                                   value))
            subject_filter_query = ' AND '.join(subject_filter)

    if measurement_information is not None:
        for name, value in measurement_information.__dict__.items():
            if name == 'group':
                name = '"group"'
            if isinstance(value, str):
                measurement_filter.append('(MES.{:} IS NULL OR MES.{:} = "{:}") '.format(name,
                                                                                         name,
                                                                                         value))
            if isinstance(value, float):
                measurement_filter.append('(MES.{:} IS NULL OR MES.{:} = {:}) '.format(name,
                                                                                       name,
                                                                                       value))
            measurement_filter_query = ' AND '.join(measurement_filter)
    additional_query = ''
    if subject_filter_query != '' or measurement_filter_query != '':
        additional_query = 'WHERE '
        if subject_filter_query != '' and measurement_filter_query != '':
            additional_query = additional_query + subject_filter_query + ' AND ' + measurement_filter_query
        if subject_filter_query == '':
            additional_query = additional_query + measurement_filter_query

    if tables is not None:
        if 'recording' in all_tables:
            extra_tables = extra_tables.join('JOIN recording REC ON REC.id_measurement = MES.id ')
            extra_outputs = extra_outputs.join('{:}.*, '.format('REC'))
            extra_join = 'and  TAB.id_recording == REC.id'

        for _table in tables:
            df = pd.read_sql_query('SELECT SUB.*, '
                                   'MES.*, '
                                   'STI.*, '
                                   '{:}'
                                   'TAB.* '
                                   'FROM subjects as SUB '
                                   'JOIN measurement_info MES ON (MES.id_subject = SUB.id) '
                                   'JOIN stimuli STI ON STI.id_measurement = MES.id '
                                   '{:}'
                                   'JOIN {:} as TAB ON TAB.id_stimuli == STI.id {:}'
                                   '{:}'.format(extra_outputs,
                                                extra_tables,
                                                _table,
                                                extra_join,
                                                additional_query),
                                   db)
            # remove duplicated columns in df
            df = df.loc[:, ~df.columns.duplicated()].copy()
            if user_query is not None:
                df = df.query(user_query)
            out[_table] = df
    else:
        if 'recording' in all_tables:
            extra_tables = extra_tables.join('JOIN recording REC ON REC.id_measurement = MES.id ')
            extra_outputs = extra_outputs.join('{:}.* '.format('REC'))
            df = pd.read_sql_query('SELECT SUB.*, '
                                   'MES.*, '
                                   'STI.*, '
                                   '{:}'
                                   'FROM subjects as SUB '
                                   'JOIN measurement_info MES ON (MES.id_subject = SUB.id) '
                                   'JOIN stimuli STI ON STI.id_measurement = MES.id '
                                   '{:}'
                                   '{:}'
                                   .format(extra_outputs,
                                           extra_tables,
                                           additional_query,
                                           ),
                                   db)
            # remove duplicated columns in df
            df = df.loc[:, ~df.columns.duplicated()].copy()
            if user_query is not None:
                df = df.query(user_query)
            out = df

    return out


def sqlite_waveforms_to_pandas(database_path: str | None = None,
                               group_factors: List[str] | None = None,
                               user_query: str | None = None,
                               tables: List[str] | None = None,
                               tables_columns: List[List[str]] | None = None,
                               channels: List[str] | None = None,
                               simuli_columns: list[str] | None = None,
                               x: str = 'x',
                               y: str = 'y',
                               x_unit: type(u.quantity) | None = None,
                               y_unit: type(u.quantity) | None = None,
                               domain_column: str = 'domain',
                               default_domain: Domain = Domain.time,
                               default_summary_function: object = np.mean
                               ) -> pd.DataFrame:
    """
    This function will return a pandas dataframe containing the waveforms for the specified group_factors.
    The data is assumed to come from a pEEGy .sqlite database.
    A pEEGy database will always contain a table 'subjects', 'measurement_info' , 'stimuli', 'recording'.
    Each subject will be linked to measurement by their id. Similarly, each measurement will be linked to each stimulus
    by its id.
    Any other table, for example, recording, waveforms, hotelling_t2_time, hotelling_t2_freq, f_test_time, f_test_freq,
    or other tables created by the user, will be uniquely related to each subject, measurement, recording, and stimuli
    by id_subject, id_measurement, id_recording, and _id_stimuli, respectively.
    This function will provide a user-friendly pandas dataframe by pooling together this information with the waveforms.
    For each grouping factor, the waveforms will be pooling together in a ndim numpy array.
    If data have not consistent number of samples, then the x axis of the first waveform for a given domain (time or
    frequency) will be used as the reference. All the rest will be interpolated and sampled to that initial x axis.
    In this way a single matrix will be returned with the data for each grouping factor.
    To avoid this last step, you should make sure that all data stored in the database are epoched having the same
    length (fixed pre_stimulus_interval and post_stimulus_interval).
    :param database_path: path to the database from which we will read the tables
    :param group_factors: a list of strings containing the groups for which you want to pool the data. For example,
    if you want to group all the waveforms from a given stimulus parameter in the stimuli table of the database (e.g.
    Amplitude and Frequency; both of which are columns in the table stimuli) you could define the group factors as
    group_factors = ['Amplitude', 'Frequency']. The returned output will then contain rows grouped by each level within
    each factor whilst the waveforms (x and y columns) will contain the data for grouped for each of these levels
    :param user_query: This parameter can be used to include or exclude data based on a logical condition, e.g.
    'subject_id != "S1"'
    :param tables: list of strings indicating the names of other generated tables that will be join to the output
    dataframe. The tables should contain 'subjects', 'measurement_info' , 'stimuli', 'recording' columns so they can
    be joined.
    :param channels: list of string specifying for which channels you want to extract the waveforms. If empty, all
    channels will be returned.
    :param simuli_columns: if not None, then it should indicate which columns to read (it can include an alias for the
     specific columns to read. For example ['channel as ch', 'subject_id as subject'] or ['channel']
    :param x: column name containing data for x-axis. This is useful to shown other data from the waveforms table
    :param y: column name containing data for y-axis. This is useful to shown other data from the waveforms table
    :param x_unit: the SI unit (e.g. u.s) if the x-axis
    :param y_unit: the SI unit (e.g. u.s) if the y-axis
    :param domain_column: name of the column indicating the domain of the data (time or frequency)
    :param default_domain: if no column indicating the domain is found, then the data will be interpreted as being in
    the default_domain
    :return: a pandas dataframe with the data grouped by group_factors.
    """
    db = sqlite3.connect(database_path)
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [_tables[0] for _tables in cursor.fetchall()]

    #  read columns from additional queries
    tables_columns_to_return = ''
    if tables is not None:
        for _table in tables:
            cursor.execute('select * FROM {:}'.format(_table))
            names = [description[0] for description in cursor.description]
            if 'data_source' in names:
                tables_columns_to_return = tables_columns_to_return.join(
                    ['{:}.{:}, '.format(_table, _column)
                     for _column in list(set(names).difference(set(['data_source'])))] +
                    [_table + '.data_source as data_source_{:}, '.format(_table)])
            else:
                tables_columns_to_return = tables_columns_to_return.join(
                    ['{:}.{:}, '.format(_table, _column)
                     for _column in list(set(names).difference(set(['data_source'])))])

    if channels is not None:
        channels_str = ','.join(['"{:}"'.format(_ch) for _ch in channels])
        channels_str = 'WAVE.channel IN ({:}) and'.format(channels_str)
    else:
        channels_str = ''

    recording_table = ''
    # extra_outputs = ''
    rec_outputs = ''
    wave_query = 'WAVE.id_stimuli = STI.id'
    if 'recording' in all_tables:
        recording_table = recording_table.join('JOIN recording REC ON REC.id_measurement = STI.id_measurement AND'
                                               ' REC.id_stimuli = STI.id ')
        # extra_outputs = extra_outputs.join('{:}.*, '.format('REC'))
        rec_outputs = 'REC.*, '
        wave_query = 'WAVE.id_stimuli = STI.id and WAVE.id_recording = REC.id'

    extra_tables = ''
    if tables is not None:
        if rec_outputs != '':
            for _table in tables:
                cursor.execute('select * FROM {:}'.format(_table))
                names = [description[0] for description in cursor.description]
                if 'channel' in names:
                    extra_tables = extra_tables.join(
                        ['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.id_recording = REC.id '
                         'and {0}.channel == WAVE.channel '
                         ''.format(_table)])
                else:
                    extra_tables = extra_tables.join(
                        ['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.id_recording = REC.id '
                         ''.format(_table)])

        else:
            extra_tables = extra_tables.join(['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.channel == WAVE.channel '
                                              ''.format(_tab) for
                                              _tab in tables])
    if simuli_columns is None:
        stim_query = 'STI.*, '
    else:
        stim_query = ''.join(['STI.{:}, '.format(_acro) for _acro in simuli_columns])

    df = pd.read_sql_query(
        'SELECT SUB.*, '
        'MES.*, '
        '{:}'
        '{:}'
        '{:}'
        'WAVE.* '
        'FROM subjects as SUB '
        'JOIN measurement_info MES ON MES.id_subject = SUB.id '
        'JOIN stimuli STI ON STI.id_measurement = MES.id '
        '{:}'
        'INNER JOIN waveforms WAVE ON ({:} '
        '{:}) '
        '{:}'.format(stim_query,
                     rec_outputs,
                     tables_columns_to_return,
                     recording_table,
                     channels_str,
                     wave_query,
                     extra_tables),
        db)
    df = df.loc[:, ~df.columns.duplicated()]
    if (domain_column in df.keys()):
        df['domain'] = df[domain_column]
    else:
        df['domain'] = default_domain
    if (x in df.keys()):
        df['x'] = df[x]
    if (y in df.keys()):
        df['y'] = df[y]
    if ('x_unit' not in df.keys()):
        df['x_unit'] = u.dimensionless_unscaled
    if ('y_unit' not in df.keys()):
        df['y_unit'] = u.dimensionless_unscaled
    if x_unit is not None:
        df['x_unit'] = x_unit
    if y_unit is not None:
        df['y_unit'] = y_unit

    if channels is not None:
        df = df[df['channel'].isin(channels)]
    if user_query is not None:
        df = df.query(user_query)
    out_pd = pd.DataFrame()
    if group_factors is None:
        group_factors = ['domain']
    else:
        group_factors = list(set.union(set(group_factors), set(['domain'])))

    groups = df.groupby(group_factors)
    n_s_time = None
    x_time = None
    n_s_freq = None
    x_freq = None
    for _group_value, _group in groups:
        y = np.array([])
        x = np.array([])
        for index, row in _group.iterrows():
            try:
                x_data = np.load(io.BytesIO(row['x']))
                y_data = np.load(io.BytesIO(row['y']))
            except ValueError:
                x_data = np.frombuffer(io.BytesIO(row['x']).read())
                y_data = np.frombuffer(io.BytesIO(row['y']).read())
            except ValueError:
                print("Could not read data from database")

            x_unit = row['x_unit']
            y_unit = row['y_unit']
            if row['domain'] == Domain.time and n_s_time is None:
                n_s_time = x_data.size
                x_time = x_data
            if row['domain'] == Domain.frequency and n_s_freq is None:
                n_s_freq = x_data.size
                x_freq = x_data
            if row['domain'] == Domain.time and n_s_time != x_data.size:
                f = interp1d(x_data, y_data, fill_value="extrapolate")
                y_data = f(x_time)
                x_data = x_time
            if row['domain'] == Domain.frequency and n_s_freq != x_data.size:
                f = interp1d(x_data, y_data, fill_value="extrapolate")
                y_data = f(x_freq)
                x_data = x_freq
            if y.size == 0:
                y = y_data
                x = x_data
            else:
                if y_data.ndim == 1:
                    y_data = y_data[:, None]
                if y.ndim == 1:
                    y = y[:, None]
                y = np.hstack((y, y_data))
            if row['domain'] == Domain.time:
                if 'fs' in row.index:
                    fs = row['fs']
                else:
                    fs = 1 / np.mean(np.diff(x))
            if row['domain'] == Domain.frequency:
                # the fs here is a guess assuming the rfft has all samples
                n = y_data.shape[0]
                if np.mod(n, 2) == 1:
                    time_size = 2 * (n - 1)
                else:
                    time_size = 2 * n + 1
                if 'fs' in row.index:
                    fs = row['fs']
                else:
                    fs = time_size / (1 / np.mean(np.diff(x)))
        pars = dict(list(zip(group_factors, _group_value)))
        # _additional_columns = {}
        # if tables_columns is not None:
        #     for _column in tables_columns:
        #         if _column in _group.keys():
        #             _additional_columns[_column] = _group[_column].values[0]

        out_pd = pd.concat([out_pd, pd.DataFrame([dict(pars, **{'x': x,
                                                                'y': y,
                                                                'x_fs': fs,
                                                                'x_unit': x_unit,
                                                                'y_unit': y_unit
                                                                }
                                                       # , **_additional_columns
                                                       )])],
                           ignore_index=True)

    if tables_columns is not None:
        summary_df = pd.DataFrame()
        for _group_value, _group in groups:
            _summary_df = pd.DataFrame()
            for _key in _group.keys():
                if is_numeric_dtype(_group[_key]):
                    _summary_df[_key] = [default_summary_function(_group[_key])]
                if is_string_dtype(_group[_key]):
                    _summary_df[_key] = _group[_key].unique()
            for _key, _value in zip(group_factors, _group_value):
                _summary_df[_key] = _value
            summary_df = pd.concat([summary_df, _summary_df])
        out_pd = pd.merge(out_pd, summary_df, on=group_factors, how='inner')

    return out_pd


def sqlite_all_waveforms_to_pandas(database_path: str | None = None,
                                   user_query: str | None = None,
                                   tables: List[str] | None = None,
                                   channels: List[str] | None = None,
                                   simuli_columns: list[str] | None = None,
                                   x: str = 'x',
                                   y: str = 'y',
                                   x_unit: type(u.quantity) | None = None,
                                   y_unit: type(u.quantity) | None = None,
                                   domain_column: str = 'domain',
                                   default_domain: Domain = Domain.time
                                   ) -> pd.DataFrame:
    """
    This function will return a pandas dataframe containing the waveforms for the specified group_factors.
    The data is assumed to come from a pEEGy .sqlite database.
    A pEEGy database will always contain a table 'subjects', 'measurement_info' , 'stimuli', 'recording'.
    Each subject will be linked to measurement by their id. Similarly, each measurement will be linked to each stimulus
    by its id.
    Any other table, for example, recording, waveforms, hotelling_t2_time, hotelling_t2_freq, f_test_time, f_test_freq,
    or other tables created by the user, will be uniquely related to each subject, measurement, recording, and stimuli
    by id_subject, id_measurement, id_recording, and _id_stimuli, respectively.
    This function will provide a user-friendly pandas dataframe by pooling together this information with the waveforms.
    For each grouping factor, the waveforms will be pooling together in a ndim numpy array.
    If data have not consistent number of samples, then the x axis of the first waveform for a given domain (time or
    frequency) will be used as the reference. All the rest will be interpolated and sampled to that initial x axis.
    In this way a single matrix will be returned with the data for each grouping factor.
    To avoid this last step, you should make sure that all data stored in the database are epoched having the same
    length (fixed pre_stimulus_interval and post_stimulus_interval).
    :param database_path: path to the database from which we will read the tables
    :param group_factors: a list of strings containing the groups for which you want to pool the data. For example,
    if you want to group all the waveforms from a given stimulus parameter in the stimuli table of the database (e.g.
    Amplitude and Frequency; both of which are columns in the table stimuli) you could define the group factors as
    group_factors = ['Amplitude', 'Frequency']. The returned output will then contain rows grouped by each level within
    each factor whilst the waveforms (x and y columns) will contain the data for grouped for each of these levels
    :param user_query: This parameter can be used to include or exclude data based on a logical condition, e.g.
    'subject_id != "S1"'
    :param tables: list of strings indicating the names of other generated tables that will be join to the output
    dataframe. The tables should contain 'subjects', 'measurement_info' , 'stimuli', 'recording' columns so they can
    be joined.
    :param channels: list of string specifying for which channels you want to extract the waveforms. If empty, all
    channels will be returned.
    :param simuli_columns: if not None, then it should indicate which columns to read (it can include an alias for the
     specific columns to read. For example ['channel as ch', 'subject_id as subject'] or ['channel']
    :param x: column name containing data for x-axis. This is useful to shown other data from the waveforms table
    :param y: column name containing data for y-axis. This is useful to shown other data from the waveforms table
    :param x_unit: the SI unit (e.g. u.s) if the x-axis
    :param y_unit: the SI unit (e.g. u.s) if the y-axis
    :param domain_column: name of the column indicating the domain of the data (time or frequency)
    :param default_domain: if no column indicating the domain is found, then the data will be interpreted as being in
    the default_domain
    :return: a pandas dataframe with the data grouped by group_factors.
    """
    db = sqlite3.connect(database_path)
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    all_tables = [_tables[0] for _tables in cursor.fetchall()]

    #  read columns from additional queries
    tables_columns_to_return = ''
    if tables is not None:
        for _table in tables:
            cursor.execute('select * FROM {:}'.format(_table))
            names = [description[0] for description in cursor.description]
            if 'data_source' in [names]:
                tables_columns_to_return = ''.join(['{:}.{:}, '.format(_table, _column)
                                                    for _column in list(set(names).difference(set(['data_source'])))] +
                                                   [_table + '.data_source as data_source_{:}, '.format(_table)])
            else:
                tables_columns_to_return = ''.join(['{:}.{:}, '.format(_table, _column)
                                                    for _column in list(set(names).difference(set(['data_source'])))])
    if channels is not None:
        channels_str = ','.join(['"{:}"'.format(_ch) for _ch in channels])
        channels_str = 'WAVE.channel IN ({:}) and'.format(channels_str)
    else:
        channels_str = ''

    recording_table = ''
    # extra_outputs = ''
    rec_outputs = ''
    wave_query = 'WAVE.id_stimuli = STI.id'
    if 'recording' in all_tables:
        recording_table = recording_table.join('JOIN recording REC ON REC.id_measurement = STI.id_measurement AND'
                                               ' REC.id_stimuli = STI.id ')
        # extra_outputs = extra_outputs.join('{:}.*, '.format('REC'))
        rec_outputs = 'REC.*, '
        wave_query = 'WAVE.id_stimuli = STI.id and WAVE.id_recording = REC.id'

    extra_tables = ''
    if tables is not None:
        if rec_outputs != '':
            for _table in tables:
                cursor.execute('select * FROM {:}'.format(_table))
                names = [description[0] for description in cursor.description]
                if 'channel' in names:
                    extra_tables = extra_tables.join(
                        ['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.id_recording = REC.id '
                         'and {0}.channel == WAVE.channel '
                         ''.format(_table)])
                else:
                    extra_tables = extra_tables.join(
                        ['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.id_recording = REC.id '
                         ''.format(_table)])
        else:
            extra_tables = extra_tables.join(['JOIN {0} ON {0}.id_stimuli = STI.id and {0}.channel == WAVE.channel '
                                              ''.format(_tab) for
                                              _tab in tables])
        # extra_outputs = extra_outputs.join(['{:}.*, '.format(_tab) for
        #                                     _tab in tables])
        # extra_outputs_data_source = extra_outputs.join(['{:}.data_source as data_source_{:}, '.format(_tab, _tab) for
        #                                     _tab in tables])
    if simuli_columns is None:
        stim_query = 'STI.*, '
    else:
        stim_query = ''.join(['STI.{:}, '.format(_acro) for _acro in simuli_columns])

    df = pd.read_sql_query(
        'SELECT SUB.*, '
        'MES.*, '
        '{:}'
        '{:}'
        '{:}'
        'WAVE.* '
        'FROM subjects as SUB '
        'JOIN measurement_info MES ON MES.id_subject = SUB.id '
        'JOIN stimuli STI ON STI.id_measurement = MES.id '
        '{:}'
        'INNER JOIN waveforms WAVE ON ({:} '
        '{:}) '
        '{:}'.format(stim_query,
                     rec_outputs,
                     tables_columns_to_return,
                     recording_table,
                     channels_str,
                     wave_query,
                     extra_tables),
        db)
    df = df.loc[:, ~df.columns.duplicated()]
    if (domain_column in df.keys()):
        df['domain'] = df[domain_column]
    else:
        df['domain'] = default_domain
    if (x in df.keys()):
        df['x'] = df[x]
    if (y in df.keys()):
        df['y'] = df[y]
    if ('x_unit' not in df.keys()):
        df['x_unit'] = u.dimensionless_unscaled
    if ('y_unit' not in df.keys()):
        df['y_unit'] = u.dimensionless_unscaled
    if x_unit is not None:
        df['x_unit'] = x_unit
    if y_unit is not None:
        df['y_unit'] = y_unit

    if channels is not None:
        df = df[df['channel'].isin(channels)]
    if user_query is not None:
        df = df.query(user_query)
    out_pd = pd.DataFrame()

    n_s_time = None
    x_time = None
    n_s_freq = None
    x_freq = None
    out_pd = df.copy()
    for index, row in df.iterrows():
        try:
            x_data = np.load(io.BytesIO(row['x']))
            y_data = np.load(io.BytesIO(row['y']))
        except ValueError:
            x_data = np.frombuffer(io.BytesIO(row['x']).read())
            y_data = np.frombuffer(io.BytesIO(row['y']).read())
        except ValueError:
            print("Could not read data from database")

        x_unit = row['x_unit']
        y_unit = row['y_unit']
        if row['domain'] == Domain.time and n_s_time is None:
            n_s_time = x_data.size
            x_time = x_data
        if row['domain'] == Domain.frequency and n_s_freq is None:
            n_s_freq = x_data.size
            x_freq = x_data
        if row['domain'] == Domain.time and n_s_time != x_data.size:
            f = interp1d(x_data, y_data, fill_value="extrapolate")
            y_data = f(x_time)
            x_data = x_time
        if row['domain'] == Domain.frequency and n_s_freq != x_data.size:
            f = interp1d(x_data, y_data, fill_value="extrapolate")
            y_data = f(x_freq)
            x_data = x_freq
        y = y_data
        x = x_data
        if row['domain'] == Domain.time:
            if 'fs' in row.index:
                fs = row['fs']
            else:
                fs = 1 / np.mean(np.diff(x))
        if row['domain'] == Domain.frequency:
            # the fs here is a guess assuming the rfft has all samples
            n = y_data.shape[0]
            if np.mod(n, 2) == 1:
                time_size = 2 * (n - 1)
            else:
                time_size = 2 * n + 1
            if 'fs' in row.index:
                fs = row['fs']
            else:
                fs = time_size / (1 / np.mean(np.diff(x)))
        # pars = dict(list(zip(group_factors, _group_value)))
        # out_pd = pd.concat([out_pd, pd.DataFrame([dict(pars, **{'x': x,
        #                                                         'y': y,
        #                                                         'x_fs': fs,
        #                                                         'x_unit': x_unit,
        #                                                         'y_unit': y_unit
        #                                                         })])],
        #                    ignore_index=True)
        out_pd.at[index, 'x'] = x
        out_pd.at[index, 'y'] = y
        out_pd.at[index, 'x_fs'] = fs
        out_pd.at[index, 'x_unit'] = x_unit
        out_pd.at[index, 'y_unit'] = y_unit

    return out_pd


def group_waveforms_df_by(df: pd.DataFrame | None = None,
                          group_by: List[str] | None = None,
                          user_query: str | None = None,
                          tables: List[str] | None = None,
                          channels: List[str] | None = None,
                          simuli_columns: list[str] | None = None,
                          default_domain: Domain = Domain.time
                          ) -> pd.DataFrame:
    """

    :return: a pandas dataframe with the data grouped by group_factors.
    """

    out_pd = pd.DataFrame()
    group_by = list(set(group_by).intersection(set(df.columns)))
    groups = df.groupby(group_by)
    for _group_value, _group in groups:
        n_s_time = None
        x_time = None
        n_s_freq = None
        x_freq = None
        _group_value_str = [str(_val) for _val in _group_value]
        print('waveform group ' + '|'.join(_group_value_str) + ': n = {:}'.format(_group.shape[0]))
        y = np.array([])
        x = np.array([])
        for index, row in _group.iterrows():
            x_data = row['x']
            y_data = row['y']
            x_unit = row['x_unit']
            y_unit = row['y_unit']
            if row['domain'] == Domain.time and n_s_time is None:
                n_s_time = x_data.size
                x_time = x_data
            if row['domain'] == Domain.frequency and n_s_freq is None:
                n_s_freq = x_data.size
                x_freq = x_data
            if row['domain'] == Domain.time and n_s_time != x_data.size:
                f = interp1d(x_data, y_data, fill_value="extrapolate")
                y_data = f(x_time)
                x_data = x_time
            if row['domain'] == Domain.frequency and n_s_freq != x_data.size:
                f = interp1d(x_data, y_data, fill_value="extrapolate")
                y_data = f(x_freq)
                x_data = x_freq
            if y.size == 0:
                y = y_data
                x = x_data
            else:
                if y_data.ndim == 1:
                    y_data = y_data[:, None]
                if y.ndim == 1:
                    y = y[:, None]
                y = np.hstack((y, y_data))
            if row['domain'] == Domain.time:
                if 'fs' in row.index:
                    fs = row['fs']
                else:
                    fs = 1 / np.mean(np.diff(x))
            if row['domain'] == Domain.frequency:
                # the fs here is a guess assuming the rfft has all samples
                n = y_data.shape[0]
                if np.mod(n, 2) == 1:
                    time_size = 2 * (n - 1)
                else:
                    time_size = 2 * n + 1
                if 'fs' in row.index:
                    fs = row['fs']
                else:
                    fs = time_size / (1 / np.mean(np.diff(x)))
        pars = dict(list(zip(group_by, _group_value)))
        out_pd = pd.concat([out_pd, pd.DataFrame([dict(pars, **{'x': x,
                                                                'y': y,
                                                                'x_fs': fs,
                                                                'x_unit': x_unit,
                                                                'y_unit': y_unit
                                                                })])],
                           ignore_index=True)
    return out_pd


def check_if_condition_exists_in_database(database_path: pathlib.Path = None,
                                          subject_information: SubjectInformation = None,
                                          measurement_information: MeasurementInformation = None,
                                          parameters: dict = None,
                                          tables: [str] = None):
    out = False
    if os.path.isfile(database_path):
        dft = sqlite_tables_to_pandas(database_path=database_path,
                                      tables=tables,
                                      subject_information=subject_information,
                                      measurement_information=measurement_information)
        # check that condition does not exist in database
        # test_df = copy.deepcopy(dft)
        for key in parameters:
            if parameters[key] is not None:
                dft = dft.loc[(dft[key] == parameters[key])]
            # print(test_df)
        if dft.shape[0] > 0:
            out = True
    return out
