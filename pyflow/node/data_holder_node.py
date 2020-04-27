from .base_node import BaseNode

import numpy as np
import pandas as pd

class DataHolderNode(BaseNode):
    
    def __init__(self, graph_uid, graph_alias, node_uid, value=None, verbose=False):
        super(DataHolderNode, self).__init__(graph_uid, graph_alias, node_uid, 'data_holder', verbose)

        self.value = value
        
    def get(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
    
    def has_value(self):
        return self.value is not None

    def get_data_dim_as_str(self):
        """Currently supports dimensionality from:

        numpy ndarray
        pandas dataframe
        pyspark dataframe

        The dimensionality of other types of data defaults to "(0)"
        """
        if not self.has_value:
            raise ValueError("There is no value!")

        if hasattr(self.value, "rdd"):

            print(self.value)
            print(self.get())
            pritn(self.get().count())
            print(self.value.count())
            print(self.value())


            dim = ((self.value.count(), len(self.value.columns)))

        elif isinstance(self.value, np.ndarray):
            dim = self.value.shape

        elif isinstance(self.value, pd.DataFrame):
            dim = self.value.shape

        else:
            return("(1, )")

        return str(dim)
        
    def __del__(self):
        if self.verbose:
            print('{} released!'.format(self.node_uid))

