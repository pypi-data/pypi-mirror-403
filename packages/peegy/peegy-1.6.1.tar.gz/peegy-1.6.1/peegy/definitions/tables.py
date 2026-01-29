from __future__ import annotations
import pandas as pd


class Tables(dict):
    def __init__(self, table_name: str | None = None,
                 data: pd.DataFrame | None = None,
                 data_source: str | None = None):
        super(Tables, self).__init__()
        self._data_source = data_source
        if table_name is not None and data is not None:
            assert data_source is not None
            if 'data_source' not in data.keys():
                data['data_source'] = data_source
            self[table_name] = data

    def __setitem__(self, key, value):
        assert isinstance(value, pd.DataFrame)
        # key = self.ensure_unique_name(label=key)
        super(Tables, self).__setitem__(key, value)
        value.name = key

    def table_names(self):
        return self.keys()

    def append(self, input_table: Tables | None = None):
        for _key in input_table.keys():
            if _key in self.keys():
                self[_key] = pd.concat([self[_key], input_table[_key]], ignore_index=True)
            else:
                self[_key] = input_table[_key]

    def tables(self):
        return self

    def get_data(self, table_name: str | None = None):
        out = None
        if table_name in self.table_names():
            out = self[table_name]
        return out
