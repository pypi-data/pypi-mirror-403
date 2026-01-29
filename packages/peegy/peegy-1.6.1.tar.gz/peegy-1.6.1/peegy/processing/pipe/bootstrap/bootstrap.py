import copy
import time
import pandas
import tqdm
from peegy.processing.pipe.definitions import InputOutputProcess
# from peegy.processing.pipe.definitions import Events
# from peegy.processing.pipe.io import GenericInputData
from peegy.processing.pipe.general import RemoveEvokedResponse
from peegy.processing.pipe.pipeline import PipePool
from peegy.definitions.tables import Tables
from peegy.processing.statistics.definitions import TestType
import numpy as np
import pandas as pd
import astropy.units as u
from peegy.processing.system.progress import ParallelTqdm
from joblib import delayed
import ray
import sys
from typing import List


class BootstrapTarget(object):
    """
    This class is used to define the target tables that will be taking for bootstrapping.
    """
    def __init__(self,
                 test_name: str | None = None,
                 group_by: List[str] | None = None,
                 target_values: List[str] | None = None
                 ):
        """

        :param table_name: What table should be targeted for bootstrapping
        :param group_by: column names (present in the target statistical table) that should be used to group
        the data that should be bootstrapped.
        :param target_values: column names with the statistics that should be bootstrapped (e.g. f)
        """
        self.test_name = test_name
        self.group_by = group_by
        self.target_values = target_values


class Bootstrap(InputOutputProcess):
    def __init__(self,
                 backend: str = 'joblib',
                 n_jobs: int | None = None,
                 origin_input_process: InputOutputProcess | None = None,
                 before_bootstrapping_input_process: InputOutputProcess | None = None,
                 at_each_bootstrap_do: PipePool | None = None,
                 n_events: int | None = None,
                 event_code: float = 1,
                 dur: u.Quantity = 100 * u.us,
                 min_time: type(u.Quantity) | None = None,
                 max_time: type(u.Quantity) | None = None,
                 epoch_length: type(u.Quantity) | None = None,
                 n_bootstraps: int = 1000,
                 bootstrap_targets: List[BootstrapTarget] | None = None,
                 alpha_level: float = 0.05,
                 one_sided: bool = True,
                 **kwargs) -> InputOutputProcess:
        """
        Bootstrap input pipeline. It assumed that the origin_input_process contains the continuous, un-epoched data.
        The events will be randomized and the pipeline passed in at_each_bootstrap_do will be run.
        The process of shuffling events and running the pipeline  will be repeated n_bootstraps times.
        The output table will contain the mean, median, standard deviation, lower confidence interval, upper confidence
        interval, sample size for the bootstrap and the p-value.
        Confidence intervals are based on the alpha_value passed.
        :param backend: which multiprocessing backend to use (ray or libjob)
        :param n_jobs: integer indicating the number of simultaneous jobs to be run.
        :param origin_input_process: The continuous, un-epoched data that will be bootstrap
        :param before_bootstrapping_input_process: Inputprocess to be run before bootstrap begins but after the
        original statistics have been computed. If None, by default the average evoked response will be removed.
        :param at_each_bootstrap_do: The pipeline that will be bootstrapped
        :param n_events: If not none, the number of random events will be n_events
        :param event_code: the event code that will be shuffled
        :param dur: duration of the shuffled event code
        :param min_time: minimum time allowed for shuffle events. If None, the timing of the first event will be used
        :param max_time: maximum time allowed for shuffle events. If None, the timing of the last event will be used
        :param epoch_length: reference duration of epochs. This is only used to ensure that the after the last event
        there will be time enough to ensure this epoch length
        :param n_bootstraps: how many times to bootstrap the pipeline
        :param bootstrap_targets: array of BootstrapTarget indicating what tables from the different pipeline elements
        should be keep for bootstrapping and what statistics.
        :param alpha_level: alpha level of confidence intervals
        :param one_sided: bool indicating whether alpha value is one_sided or not.
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(Bootstrap, self).__init__(input_process=None, **kwargs)
        self.backend = backend
        self.n_jobs = n_jobs
        self.origin_input_process = origin_input_process
        self.before_bootstrapping_input_process = before_bootstrapping_input_process
        self.at_each_bootstrap_do = at_each_bootstrap_do
        self.n_bootstraps = n_bootstraps
        self.n_events = n_events
        self.event_code = event_code
        self.dur = dur
        self.min_time = min_time
        self.max_time = max_time
        self.epoch_length = epoch_length
        self.alpha_level = alpha_level
        self.one_sided = one_sided
        self._original_events = None
        self.bootstrap_targets = bootstrap_targets
        self._origin_input_process = None
        self._at_each_bootstrap_do = None

    def transform_data(self):
        # the origin input_process is copied to ensure nothing is done to the original reference process
        self._at_each_bootstrap_do = copy.deepcopy(self.at_each_bootstrap_do)
        if self.origin_input_process is not None:
            self._origin_input_process = copy.deepcopy(self.origin_input_process)
        else:
            self._origin_input_process = copy.deepcopy(list(self._at_each_bootstrap_do.values())[0].input_process)
        # ensure that the reference process is used by the pipeline
        for _key, _process in list(self._at_each_bootstrap_do.items()):
            if _process.input_process.name == self._origin_input_process.name:
                self._at_each_bootstrap_do[_key].input_process = self._origin_input_process

        # first run pipeline to extract actual values to be tested against bootstrapped tables
        self._at_each_bootstrap_do.run(force=True)
        # extract reference tables
        ref_table = get_tables(pipeline=self._at_each_bootstrap_do, targets=self.bootstrap_targets)
        # get event information
        _n_events = self.n_events
        _min_time = self.min_time
        _max_time = self.max_time
        if _n_events is None:
            _n_events = self._origin_input_process.output_node.events.get_events_code(code=self.event_code).size
        if _min_time is None:
            _min_time = self._origin_input_process.output_node.events.get_events_time(code=self.event_code).min()
        if _max_time is None:
            _max_time = self._origin_input_process.output_node.events.get_events_time(code=self.event_code).max()
        # apply whatever we ask before we bootstrap. Normally we will remove the evoked data
        if self.before_bootstrapping_input_process is not None:
            self.before_bootstrapping_input_process.input_process = self._origin_input_process
        else:
            self.before_bootstrapping_input_process = RemoveEvokedResponse(
                input_process=self._origin_input_process,
                event_code=self.event_code,
                post_stimulus_interval=self.epoch_length)

        self.before_bootstrapping_input_process.run()
        self._origin_input_process.output_node.data = self.before_bootstrapping_input_process.output_node.data
        # generate average epoch length if not given to prevent small estimations from random events
        _epoch_length = self.epoch_length
        if self.epoch_length is None:
            _epoch_length = np.mean(
                np.diff(self._origin_input_process.output_node.events.get_events_time(code=self.event_code)))

        # bootstrap pipeline
        start_time = time.time()
        bootstrapped_tables = self.bootstrap_pipeline(backend=self.backend,
                                                      n_jobs=self.n_jobs,
                                                      event_code=self.event_code,
                                                      dur=self.dur,
                                                      epoch_length=_epoch_length,
                                                      min_time=_min_time,
                                                      max_time=_max_time,
                                                      n_events=_n_events,
                                                      )
        end_time = time.time()
        print('Bootstrapping took {:1.3} seconds'.format(end_time - start_time))
        # compute statistics
        print('Generating statistical table')
        boots_df = table_list_to_pd(tables=bootstrapped_tables, targets=self.bootstrap_targets)
        ref_table = ref_table.rename(columns={'value': 'statistic_value'})
        columns_left = set(boots_df.keys()).difference(['value'])
        columns_right = set(ref_table.keys()).difference(['statistic_value'])
        common_cols = list(columns_left.intersection(columns_right))
        bootstrapped_and_ref_tables = pd.merge(boots_df,
                                               ref_table,
                                               how='left',
                                               on=common_cols,
                                               )

        df_boots = bootstrapped_and_ref_tables.groupby(list(set(bootstrapped_and_ref_tables.keys()).difference(
            ['value', 'statistic_value'])), as_index=False, dropna=False).apply(
            lambda x: pd.Series({'stats': get_bootstrap_estimates(samples=x['value'],
                                                                  statistic=x['statistic_value'],
                                                                  alpha_level=self.alpha_level,
                                                                  one_sided=self.one_sided)}))

        (df_boots['statistic_value'],
         df_boots['mean'],
         df_boots['median'],
         df_boots['std'],
         df_boots['ci_lower'],
         df_boots['ci_upper'],
         df_boots['sample_size'],
         df_boots['p_value']) = zip(*df_boots.stats)
        df_boots['one_sided'] = self.one_sided
        df_boots['data_source_bootstrap'] = df_boots['data_source']
        df_boots = df_boots.drop(['stats', 'data_source'], axis=1)
        df_boots['n_epochs'] = _n_events
        # join boot table and reference table
        self.output_node.statistical_tests = Tables(table_name=TestType.bootstrap,
                                                    data=df_boots,
                                                    data_source=self.name)

    def bootstrap_pipeline(self,
                           n_jobs: int | None = None,
                           epoch_length: type(u.Quantity) | None = None,
                           n_events: int | None = None,
                           event_code: float = 1,
                           dur: u.Quantity = 100 * u.us,
                           min_time: type(u.Quantity) | None = None,
                           max_time: type(u.Quantity) | None = None,
                           backend: str = 'joblib'
                           ):
        if n_jobs is None:
            n_jobs = 1
        bootstrapped_tables = []
        if backend == 'ray':
            # multiprocessing bootstrap via ray
            ray.shutdown()
            if not ray.is_initialized():
                if 'sphinx' in sys.modules:
                    # this is a protection for when building with sphinx
                    sys.stdout.fileno = lambda: False
                ray.init(log_to_driver=False)
            ref_data = ray.put(self._origin_input_process.output_node.data.copy())
            self._origin_input_process.input_node.data = None
            self._origin_input_process.output_node.data = None
            for _, _value in self._at_each_bootstrap_do.items():
                _value.input_node.data = None
                _value.output_node.data = None
            reference_pool_id = self._at_each_bootstrap_do
            target_tables = self.bootstrap_targets
            ref_process = self._origin_input_process

            subs = np.maximum(self.n_bootstraps // n_jobs, 1)
            n_boots = np.array([subs] * n_jobs)
            _current_number = np.sum(n_boots)
            if _current_number < self.n_bootstraps:
                n_boots[-1] = n_boots[-1] + self.n_bootstraps - _current_number
            result_ids = [ray_worker_bootstrap_pool.options(num_cpus=n_jobs).remote(
                ref_process=ref_process,
                ref_data=ref_data,
                pipe_pool=reference_pool_id,
                bootstrap_targets=target_tables,
                event_code=event_code,
                dur=dur,
                epoch_length=epoch_length,
                min_time=min_time,
                max_time=max_time,
                n_boots=n_boots[_i],
                n_events=n_events) for _i in range(n_jobs)]
            results = [result for result in tqdm.tqdm(to_iterator(result_ids),
                                                      total=len(result_ids),
                                                      desc='Bootstrapping/worker',
                                                      colour='blue',
                                                      miniters=0)]
            ray.shutdown()
            for _r in results:
                bootstrapped_tables = bootstrapped_tables + _r
        elif backend == 'joblib':
            # multiprocessing bootstrap via joblib
            ref_data = self._origin_input_process.output_node.data.copy()
            if self._origin_input_process.input_node is not None:
                self._origin_input_process.input_node.data = None

            if self._origin_input_process.output_node is not None:
                self._origin_input_process.output_node.data = None
            for _, _value in self._at_each_bootstrap_do.items():
                _value.input_node.data = None
                _value.output_node.data = None
            reference_pool_id = self._at_each_bootstrap_do
            target_tables = self.bootstrap_targets
            # ref_process = copy.deepcopy(self._origin_input_process)
            ref_process = self._origin_input_process

            subs = np.maximum(self.n_bootstraps // n_jobs, 1)
            n_boots = np.array([subs] * n_jobs)
            _current_number = np.sum(n_boots)
            if _current_number < self.n_bootstraps:
                n_boots[-1] = n_boots[-1] + self.n_bootstraps - _current_number

            results = ParallelTqdm(total=n_jobs,
                                   desc='Bootstrapping/worker',
                                   n_jobs=n_jobs,
                                   mmap_mode='r',
                                   colour='blue',
                                   # backend='threading'
                                   )(
                delayed(worker_bootstrap_pool)(
                    ref_process=ref_process,
                    ref_data=ref_data,
                    pipe_pool=reference_pool_id,
                    bootstrap_targets=target_tables,
                    event_code=self.event_code,
                    epoch_length=epoch_length,
                    min_time=min_time,
                    max_time=max_time,
                    n_boots=n_boots[_i],
                    n_events=n_events
                ) for _i in range(n_jobs))
            for _r in results:
                bootstrapped_tables = bootstrapped_tables + _r
        return bootstrapped_tables


def to_iterator(obj_ids):
    while obj_ids:
        done, obj_ids = ray.wait(obj_ids)
        _result = ray.get(done[0])
        yield _result


@ray.remote
def ray_worker_bootstrap_pool(ref_process: InputOutputProcess | None = None,
                              ref_data: type(np.array) | None = None,
                              pipe_pool: PipePool | None = None,
                              bootstrap_targets: List[BootstrapTarget] | None = None,
                              epoch_length: type(u.Quantity) | None = None,
                              n_events: int | None = None,
                              event_code: float = 1,
                              dur: u.Quantity = 100 * u.us,
                              min_time: type(u.Quantity) | None = None,
                              max_time: type(u.Quantity) | None = None,
                              n_boots: int | None = None
                              ):
    tables = worker_bootstrap_pool(ref_process=ref_process,
                                   ref_data=ref_data,
                                   pipe_pool=pipe_pool,
                                   bootstrap_targets=bootstrap_targets,
                                   epoch_length=epoch_length,
                                   n_events=n_events,
                                   event_code=event_code,
                                   dur=dur,
                                   min_time=min_time,
                                   max_time=max_time,
                                   n_boots=n_boots)
    return tables


def worker_bootstrap_pool(ref_process: InputOutputProcess | None = None,
                          ref_data: type(np.array) | None = None,
                          pipe_pool: PipePool | None = None,
                          bootstrap_targets: List[BootstrapTarget] | None = None,
                          epoch_length: type(u.Quantity) | None = None,
                          n_events: int | None = None,
                          event_code: float = 1,
                          dur: u.Quantity = 100 * u.us,
                          min_time: type(u.Quantity) | None = None,
                          max_time: type(u.Quantity) | None = None,
                          n_boots: int | None = None
                          ):
    ref_process.output_node.data = ref_data
    _local_pipe_pool = PipePool()
    for _key, _value in pipe_pool.items():
        _parameters = _value.get_input_parameters()
        if _parameters['input_process'].name == ref_process.name:
            _parameters['input_process'] = ref_process
        if _parameters['input_process'].name in _local_pipe_pool.keys():
            _parameters['input_process'] = _local_pipe_pool[_parameters['input_process'].name]
        _local_pipe_pool[_key] = type(_value)(**_parameters)

    bootstrapped_tables = []
    print(n_boots)
    for _i in tqdm.tqdm(range(n_boots),
                        total=n_boots,
                        desc='worker-bootstrapping',
                        colour='blue',
                        miniters=0):

        ref_process.output_node.randomize_events(event_code=event_code,
                                                 epoch_length=epoch_length,
                                                 min_time=min_time,
                                                 max_time=max_time,
                                                 dur=dur,
                                                 n_events=n_events
                                                 )

        _local_pipe_pool.run(force=True)
        _current_tables = catch_tables(pipeline=_local_pipe_pool, targets=bootstrap_targets)
        bootstrapped_tables = bootstrapped_tables + _current_tables
    return bootstrapped_tables


def get_bootstrap_estimates(samples: type(np.array) | None = None,
                            statistic: type(np.array) | None = None,
                            alpha_level: float = 0.05,
                            one_sided=True):
    # remove nan that may be present
    samples = np.array(samples[~pd.isna(samples)])
    statistic_value = np.unique(statistic)
    assert statistic_value.size == 1
    sample_size = samples.shape[0]
    sorted_samples = np.sort(samples, axis=0)
    mean = np.mean(samples, axis=0)
    median = np.median(samples, axis=0)
    std = np.std(samples, axis=0)
    _alpha = alpha_level
    if not one_sided:
        _alpha = alpha_level / 2.0

    _i_upper = np.minimum(int(samples.shape[0] * (1 - _alpha)), samples.shape[0])
    _i_lower = np.maximum(int(samples.shape[0] * _alpha), 0)
    ci_lower = sorted_samples[_i_lower]
    ci_upper = sorted_samples[_i_upper]
    diff = np.abs(statistic_value - sorted_samples)
    _idx_match = np.argmin(diff, axis=0) + 1
    p_value = 1 - _idx_match / sample_size
    return [statistic_value[0], mean, median, std, ci_lower, ci_upper, sample_size, p_value]


def get_tables(pipeline: PipePool | None = None,
               targets: List[BootstrapTarget] | None = None):
    output = pd.DataFrame()
    for _source, _value in pipeline.items():
        for _target in targets:
            for _key, df in _value.output_node.statistical_tests.items():
                if _target.test_name in df['test_name'].values:
                    _columns = list(set(df.keys()) &
                                    set(_target.target_values))
                    if len(_columns):
                        df = df[_target.group_by + _target.target_values + ['data_source', 'test_name']]
                        melted_df = pd.melt(df,
                                            ignore_index=False,
                                            id_vars=set(set(df.keys())).difference(_target.target_values),
                                            value_vars=_target.target_values,
                                            var_name='statistic',
                                            value_name='value')
                        output = pandas.concat([output, melted_df], ignore_index=True)
    return output


def catch_tables(pipeline: PipePool | None = None,
                 targets: List[BootstrapTarget] | None = None):
    output = []
    for _source, _value in pipeline.items():
        for _target in targets:
            for _key, df in _value.output_node.statistical_tests.items():
                if _target.test_name in df['test_name'].values:
                    _columns = list(set(df.keys()) &
                                    set(_target.target_values))
                    if len(_columns):
                        output.append(df)
    return output


def table_list_to_pd(tables: List[pd.DataFrame] | None = None,
                     targets: List[BootstrapTarget] | None = None):
    output = pd.DataFrame()
    for _target in targets:
        df = pd.concat([_t for _t in tables if _target.test_name in _t['test_name'].values])
        df = df[_target.group_by + _target.target_values + ['data_source', 'test_name']]
        melted_df = pd.melt(df, ignore_index=False,
                            id_vars=set(set(df.keys())).difference(_target.target_values),
                            value_vars=_target.target_values,
                            var_name='statistic')
        output = pandas.concat([output, melted_df], ignore_index=True)
    return output
