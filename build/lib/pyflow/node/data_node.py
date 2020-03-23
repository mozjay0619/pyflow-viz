from .base_node import BaseNode
from .data_holder_node import DataHolderNode

import warnings


class DataNode(BaseNode):
    
    def __init__(self, node_uid, value=None, persist=False, verbose=False, alias=None):
        super(DataNode, self).__init__(node_uid, 'data', verbose, alias or 'data')
        
        self.value_holder = DataHolderNode(self.node_uid, value, self.verbose)
        self.data_persist = persist

    def set_value(self, value):
        
        self.value_holder.set_value(value)
        
    def has_value(self):
        
        return self.value_holder.has_value()
        
    def is_persisted(self):
        
        return self.data_persist

    def get(self):
        
        if self.value_holder.has_value():
            return self.value_holder.get()
        else:
            if self.verbose:
                print('computing for {}'.format(self.node_uid))
            
            self.activate_dependency_op_nodes()
            self.parent_node_weak_refs[0]().run()
            return self.value_holder.get()

    def activate_dependency_op_nodes(self):
        
        dependency_ancestor_node_weak_refs = self.get_dependency_ancestor_node_weak_refs()
        dependency_op_nodes_weak_refs = [elem for elem in dependency_ancestor_node_weak_refs 
                                  if elem().node_type == 'operation']
        
        for dependency_op_node_weak_ref in dependency_op_nodes_weak_refs:
            dependency_op_node_weak_ref().activate()

    def get_dependency_ancestor_node_weak_refs(self):

        ancestors_weak_refs = list()
        DataNode._get_dependency_ancestor_node_weak_refs(self, ancestors_weak_refs)
        return ancestors_weak_refs
    
    @staticmethod
    def _get_dependency_ancestor_node_weak_refs(self, acc):
        """
        all data nodes needed that has no values,
        all op until valued data nodes
        """

        for parent_node_weak_ref in self.get_parent_node_weak_refs():

            if parent_node_weak_ref().node_type == 'data' and parent_node_weak_ref().has_value():
                continue

            if parent_node_weak_ref().has_parent_node_weak_refs():
                
                if parent_node_weak_ref not in acc:
                    acc.append(parent_node_weak_ref)
                DataNode._get_dependency_ancestor_node_weak_refs(parent_node_weak_ref(), acc)

            else:

                acc.append(parent_node_weak_ref)

    def release_memory(self):
        
        if self.is_persisted():
            warnings.warn("You are releasing a DataNode that was persisted!", RuntimeWarning)
        
        del self.value_holder
        self.value_holder = DataHolderNode(self.node_uid, None, self.verbose)
        
        