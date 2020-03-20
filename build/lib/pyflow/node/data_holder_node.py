from .base_node import BaseNode

class DataHolderNode(BaseNode):
    
    def __init__(self, node_uid, value=None, verbose=False):
        super(DataHolderNode, self).__init__(node_uid, 'data_holder', verbose)

        self.value = value
        
    def get(self):
        return self.value
    
    def set_value(self, value):
        self.value = value
    
    def has_value(self):
        return self.value is not None
        
    def __del__(self):
        if self.verbose:
            print('{} released!'.format(self.node_uid))
