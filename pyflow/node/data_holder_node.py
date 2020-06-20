from .base_node import BaseNode

import numpy as np
import pandas as pd


class DataHolderNode(BaseNode):
    
    def __init__(self, graph_uid, graph_alias, node_uid, value=None, verbose=False):
        super(DataHolderNode, self).__init__(graph_uid, graph_alias, node_uid, 'data_holder', verbose)

        self.value = value
        self.dim = None
        
    def get(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
    
    def has_value(self):
        return self.value is not None

    def get_persisted_data_dim_as_str(self):
        """Currently supports dimensionality from:

        numpy ndarray
        pandas dataframe
        pyspark dataframe

        The dimensionality of other types of data defaults to "(0)"
        """
        if not self.has_value:
            raise ValueError("There is no value!")

        if self.dim is not None:
            return self.dim

        if hasattr(self.value, "rdd"):
            row_cnt = self.get().persist().count()
            col_cnt = len(self.get().columns)
            self.dim = (row_cnt, col_cnt)

        elif isinstance(self.value, np.ndarray):
            self.dim = self.value.shape

        elif isinstance(self.value, pd.DataFrame):
            self.dim = self.value.shape

        else:
            self.dim = "(1, )"

        return str(self.dim)
        
    def __del__(self):
        if self.verbose:
            print('{} released!'.format(self.node_uid))
