

class TestType(object):
    hotelling_t2_time = 'hotelling_t2_time'  # hotelling-t2 test in the time-domain
    hotelling_t2_freq = 'hotelling_t2_freq'  # hotelling-t2 test in the frequency-domain
    f_test_freq = 'f_test_freq'  # f-ratio in frequency domain
    f_test_time = 'f_test_time'  # f-ratio using multiple points in the time-domain
    rayleigh_test = 'rayleigh_test'  # phase-locking value
    covariance = 'covariance'  # covariance
    bootstrap = 'bootstrap'

    def get_available_methods(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return members


class HotellingTSquareFrequencyTest(object):
    def __init__(self,
                 data_source: str | None = None,
                 test_name='HT2',
                 frequency_tested=None,
                 df_1=None,
                 df_2=None,
                 t_square=None,
                 f=None,
                 p_value=None,
                 n_epochs=None,
                 spectral_magnitude=None,
                 spectral_phase=None,
                 rn=None,
                 snr=None,
                 snr_db=None,
                 f_critic=None,
                 channel=None,
                 ini_time: float | None = None,
                 end_time: float | None = None
                 ):
        self.data_source = data_source
        self.test_name = test_name
        self.frequency_tested = frequency_tested
        self.df_1 = df_1
        self.df_2 = df_2
        self.t_square = t_square
        self.f = f
        self.p_value = p_value
        self.spectral_magnitude = spectral_magnitude
        self.spectral_phase = spectral_phase
        self.rn = rn
        self.n_epochs = n_epochs
        self.snr = snr
        self.snr_db = snr_db
        self.f_critic = f_critic
        self.channel = channel
        self.ini_time = ini_time
        self.end_time = end_time


class HotellingTSquareTest(object):
    def __init__(self,
                 test_name='HT2',
                 df_1=None,
                 df_2=None,
                 t_square=None,
                 f=None,
                 f_critic=None,
                 p_value=None,
                 mean_amplitude=None,
                 mean_phase=None,
                 rn=None,
                 n_epochs=None,
                 snr=None,
                 snr_db=None,
                 snr_critic_db=None,
                 snr_critic=None,
                 channel=None,
                 frequency_tested=None,
                 ini_time: float | None = None,
                 end_time: float | None = None,
                 **kwargs
                 ):
        self.test_name = test_name
        self.df_1 = df_1
        self.df_2 = df_2
        self.t_square = t_square
        self.f = f
        self.f_critic = f_critic
        self.p_value = p_value
        self.mean_amplitude = mean_amplitude
        self.mean_phase = mean_phase
        self.rn = rn
        self.n_epochs = n_epochs
        self.snr = snr
        self.snr_db = snr_db
        self.snr_critic_db = snr_critic_db
        self.snr_critic = snr_critic
        self.channel = channel
        self.frequency_tested = frequency_tested
        self.ini_time = ini_time
        self.end_time = end_time
        for _item, _value in kwargs.items():
            setattr(self, _item, _value)


class FrequencyFTest(object):
    def __init__(self,
                 test_name='F-test',
                 frequency_tested=None,
                 df_1=None,
                 df_2=None,
                 f=None,
                 p_value=None,
                 spectral_magnitude=None,
                 spectral_phase=None,
                 rn=None,
                 bn=None,
                 snr=None,
                 snr_db=None,
                 f_critic=None,
                 channel=None,
                 ini_time: float | None = None,
                 end_time: float | None = None,
                 ):
        self.test_name = test_name
        self.frequency_tested = frequency_tested
        self.df_1 = df_1
        self.df_2 = df_2
        self.f = f
        self.p_value = p_value
        self.spectral_magnitude = spectral_magnitude
        self.spectral_phase = spectral_phase
        self.rn = rn
        self.bn = bn
        self.snr = snr
        self.snr_db = snr_db
        self.f_critic = f_critic
        self.channel = channel
        self.ini_time = ini_time
        self.end_time = end_time


class PhaseLockingValueTest(object):
    def __init__(self,
                 test_name='rayleigh_test',
                 plv=None,
                 df_1=None,
                 z_value=None,
                 z_critic=None,
                 p_value=None,
                 mean_phase=None,
                 channel=None,
                 frequency_tested=None,
                 ini_time: float | None = None,
                 end_time: float | None = None,
                 rn=None):
        self.test_name = test_name
        self.plv = plv
        self.df_1 = df_1
        self.z_value = z_value
        self.z_critic = z_critic
        self.p_value = p_value
        self.mean_phase = mean_phase
        self.channel = channel
        self.frequency_tested = frequency_tested
        self.rn = rn
        self.ini_time = ini_time
        self.end_time = end_time


class FmpTest(object):
    def __init__(self,
                 test_name='Fmp',
                 label: str | None = None,
                 df_1: float | None = None,
                 df_2: float | None = None,
                 f: float | None = None,
                 f_critic: float | None = None,
                 p_value: float | None = None,
                 rn: float | None = None,
                 snr: float | None = None,
                 ini_time: float | None = None,
                 end_time: float | None = None,
                 n_epochs: int | None = None,
                 channel: str | None = None):
        self.test_name = test_name
        self.label = label
        self.df_1 = df_1
        self.df_2 = df_2
        self.f = f
        self.f_critic = f_critic
        self.p_value = p_value
        self.rn = rn
        self.snr = snr
        self.ini_time = ini_time
        self.end_time = end_time
        self.n_epochs = n_epochs
        self.channel = channel
