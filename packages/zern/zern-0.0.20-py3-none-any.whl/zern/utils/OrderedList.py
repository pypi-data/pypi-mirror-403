from datetime import datetime
import numpy as np
import pickle

def load_dict(path):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return OrderedList(data)

class OrderedList:
    class _ILOC:
        def __init__(self,parent) -> None:
            self.parent = parent
        
        def __getitem__(self, obj):
            if isinstance(obj, int):
                data_head = {key: [value[obj]] for key, value in self.parent._data.items()}
                return OrderedList(data_head)
            elif isinstance(obj, slice):
                data_head = {key: value[obj.start:obj.stop:obj.step] for key, value in self.parent._data.items()}
                return OrderedList(data_head)

    def __init__(self,list_of_values) -> None:
        if type(list_of_values) is dict:
            self._data = list_of_values
        else:
            self._data = self._basic_method(list_of_values=list_of_values)
        self.columns = list(self._data.keys())
        self.iloc = self._ILOC(self)
    
    def __repr__(self) -> str:
        return self.print_dict_as_table(self._data)
    
    def _basic_method(self,list_of_values):
        mod_func = lambda date_string: datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
        nd = {'datetime':[],'open':[],'high':[],'low':[],'close':[],'volume':[],'oi':[]}
        for row in list_of_values:
            nd['datetime'].append(mod_func(row[0]))
            nd['open'].append(row[1])
            nd['high'].append(row[2])
            nd['low'].append(row[3])
            nd['close'].append(row[4])
            nd['volume'].append(row[5])
            nd['oi'].append(row[6])
        return nd
    
    def print_dict_as_table(self,data,trucation=7):
        prints = []
        max_lengths = [max(len(str(value)) for value in col) for col in data.values()]
        header_row = "  |  ".join(header.center(length) for header, length in zip(data.keys(), max_lengths))
        #print(header_row)
        prints.append(header_row)
        separator = "--+--".join("-" * length for length in max_lengths)
        #print(separator)
        prints.append(separator)
        counter = 0
        more_rows = False
        for i in range(len(next(iter(data.values())))):
            row_values = [str(data[key][i]).center(length) for key, length in zip(data.keys(), max_lengths)]
            row = "  |  ".join(row_values)
            #print(row)
            if counter <= trucation:
                prints.append(row)
            else:
                more_rows = True
            counter += 1
        if more_rows:
            prints.append('... upto {} rows'.format(counter))
        return '\n'.join(prints)

    def head(self, val=5):
        data_head = {key: value[:val] for key, value in self._data.items()}
        return OrderedList(data_head)
    
    def tail(self, val=5):
        data_head = {key: value[-val:] for key, value in self._data.items()}
        return OrderedList(data_head)
    
    def __getitem__(self,list_of_columns):
        if type(list_of_columns) is str:
            data_head = {list_of_columns: self._data[list_of_columns]}
        elif type(list_of_columns) is list:
            data_head = {key: self._data[key] for key in list_of_columns}
        return OrderedList(data_head)
    
    @property
    def values(self):
        data_head = [self._data[key] for key in self._data.keys()]
        return np.array(data_head).T
    
    def save(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self._data, f)
    
    def __len__(self):
        return len(self._data['datetime'])