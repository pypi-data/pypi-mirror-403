import time
import tqdm
from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.storage import SaveToDatabase
from peegy.definitions.events import Events
import numpy as np
from typing import List


class EpochsByStep(InputOutputProcess):
    def __init__(self,
                 origin_input_processes: List[InputOutputProcess] | None = None,
                 at_each_epoch_block_do: PipePool | None = None,
                 epochs_step_size: int = 2,
                 max_epochs: int | None = None,
                 deep_break: bool = True,
                 event_code: float | None = None,
                 include_all_epochs: bool = False,
                 **kwargs) -> InputOutputProcess:
        """
        Process input pipeline by blocks of epochs. It assumed that the origin_input_process an EpochData class
        (epoched data).
        :param origin_input_processes: List of InputProcess holding all the data (in epochs, or events) which will be
        used for epoch iterations
        :param at_each_epoch_block_do: The pipeline that will be processed by epochs blocks
        :param epochs_step_size: indicate the step size to run the pipeline. The number of epochs will increase by this
        number at each run.
        :param deep_break: if True, epochs block will be extracted across all possible data. This means that if you
        have 100 epochs and epochs_step_size = 2, then epochs 0-1, 2-3, ..., 99-100, then 0-3, 4-7, ..., 97-100,
        ... until 0-100 will be run when deep_break is true. Otherwise, we will only extract 0-1, 0-3, ..., 0-99 epoch
        blocks (i.e., a progressive number of epochs per iteration).
        :param event_code: event code to be use in the case that something needs to be epoched
        :param include_all_epochs: if False, the number of epochs to be processed will be strictly spaced by
        epochs_step_size until max_epochs is reached.
        If include_all_epochs is set to True, epochs will be process at each epochs_step_size < max_epochs. However,
        it will also include an additional block including all epochs.
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(EpochsByStep, self).__init__(input_process=None, **kwargs)
        self.origin_input_processes = origin_input_processes
        self.at_each_epoch_block_do = at_each_epoch_block_do
        self.epochs_step_size = epochs_step_size
        self.max_epochs = max_epochs
        self.deep_break = deep_break
        self.event_code = event_code
        self.include_all_epochs = include_all_epochs
        self._origin_input_process = None
        self.last_run = None
        self._data_containers = []
        self._event_containers = []
        self._n_epochs = None

    def transform_data(self):
        # the origin input_process is copied to ensure nothing is done to the original reference process
        n_epochs = []
        if self.origin_input_processes is None:
            _process = self.at_each_epoch_block_do[list(self.at_each_epoch_block_do)[0]].input_process
            self.origin_input_processes = [_process]
            print('No origin_input_processes provided. '
                  'Using {:} as origin data source (from at_each_epoch_block_do)'.format(_process.name))
        for _process in self.origin_input_processes:
            if _process.output_node.data.ndim == 3:
                self._data_containers.append(
                    {'process': _process,
                     'original_data': _process.output_node.data.copy()})
                n_epochs.append(_process.output_node.data.shape[2])
            if _process.output_node.data.ndim == 2 and _process.output_node.events is not None:
                self._event_containers.append(
                    {'process': _process,
                     'original_events': _process.output_node.events.get_events(code=self.event_code)})
                n_epochs.append(len(_process.output_node.events.get_events(code=self.event_code)))

        if np.unique(np.array(n_epochs)).size > 1:
            print('The origin_input_processes have different number of epochs: {:}. '
                  'Using the minimum to proceed.'.format(n_epochs))

        self._n_epochs = np.min(np.array(n_epochs))
        start_time = time.time()
        self.pipeline_per_epoch_block()
        end_time = time.time()
        print('Per epoch pipeline took{:1.3} seconds'.format(end_time - start_time))

    def pipeline_per_epoch_block(self):
        pipe_pool = self.at_each_epoch_block_do
        epochs_step_size = self.epochs_step_size
        max_epochs = self.max_epochs
        include_all_epochs = self.include_all_epochs

        if max_epochs is None:
            max_epochs = self._n_epochs
        # defines the maximum number of epoch.
        n_epochs = np.arange(epochs_step_size,
                             max_epochs + epochs_step_size,
                             epochs_step_size)
        n_epochs = n_epochs[np.argwhere(n_epochs <= self._n_epochs).flatten()]
        if include_all_epochs:
            n_epochs = np.concatenate((n_epochs, [self._n_epochs]))
        n_epochs = np.unique(n_epochs)
        _local_pipe_pool = pipe_pool
        for _epochs in tqdm.tqdm(n_epochs, desc='Processing epochs', colour='blue'):
            _n_epochs_range = np.minimum(self._n_epochs, max_epochs)
            n_blocks = int(_n_epochs_range / _epochs)
            ini_b = np.arange(0, n_blocks * _epochs, _epochs).astype(int)
            end_b = np.minimum(ini_b + int(_epochs),
                               _n_epochs_range).astype(int)
            if self.deep_break:
                _epoch_groups = zip(ini_b, end_b)
            else:
                _epoch_groups = zip([ini_b[0]], [end_b[0]])

            for _block, (_ini_b, _end_b) in tqdm.tqdm(enumerate(_epoch_groups),
                                                      desc='epoch size: {:}'.format(_epochs)):
                # update origing references
                for _process in self._data_containers:
                    _process['process'].output_node.data = _process['original_data'][:, :, _ini_b: _end_b]
                    _n_epochs = _process['process'].output_node.data.shape[2]
                for _process in self._event_containers:
                    _events_to_use = _process['original_events'][_ini_b: _end_b]
                    _process['process'].output_node.events = Events(events=_events_to_use)
                    _n_epochs = _process['process'].output_node.events.get_events().size
                for _key, _value in pipe_pool.items():
                    if isinstance(_local_pipe_pool[_key], SaveToDatabase):
                        _local_pipe_pool[_key].stimuli_information['n_epochs'] = _n_epochs
                        _local_pipe_pool[_key].stimuli_information['epoch_block'] = _block
                _local_pipe_pool.run(force=True)

        # assign last run
        self.last_run = _local_pipe_pool
