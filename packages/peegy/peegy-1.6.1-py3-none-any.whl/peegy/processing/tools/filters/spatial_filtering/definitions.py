

class FilterType(object):
    dss = 'dss'  # hotelling-t2 test in the time-domain

    def get_available_methods(self):
        members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
        return members


class DSSData(object):
    def __init__(self,
                 filter_type='DSS',
                 bias_frequencies=None,
                 bias_domain=None,
                 unbiased_power=None,
                 biased_power=None,
                 total_unbiased_power=None,
                 total_biased_power=None,
                 n_components_rotation_1=None,
                 n_components_rotation_2=None,
                 n_possible_components=None,
                 threshold=None,
                 component_rank=None,
                 power_ratio=None,
                 kept=True,
                 main_channel=None):
        self.filter_type = filter_type
        self.bias_frequencies = bias_frequencies
        self.bias_domain = bias_domain
        self.unbiased_power = unbiased_power
        self.biased_power = biased_power
        self.total_unbiased_power = total_unbiased_power
        self.total_biased_power = total_biased_power
        self.n_components_rotation_1 = n_components_rotation_1
        self.n_components_rotation_2 = n_components_rotation_2
        self.n_possible_components = n_possible_components
        self.threshold = threshold
        self.component_rank = component_rank
        self.power_ratio = power_ratio
        self.kept = kept
        self.main_channel = main_channel
