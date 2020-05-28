from .base_node import BaseNode
from .data_holder_node import DataHolderNode

import warnings


class DataNode(BaseNode):
    
    def __init__(self, graph_uid, graph_alias, node_uid, value=None, persist=False, verbose=False, alias=None, graph_dict=None):
        super(DataNode, self).__init__(graph_uid, graph_alias, node_uid, 'data', verbose, alias or 'data')
        
        self.value_holder = DataHolderNode(graph_uid, graph_alias, self.node_uid, value, self.verbose)

        self.data_persist = persist
        self.graph_uid = graph_uid
        self.graph_alias = graph_alias

        self.graph_dict = graph_dict

    def set_value(self, value):
        
        self.value_holder.set_value(value)
        
    def has_value(self):
        
        return self.value_holder.has_value()

    def persist(self):

        self.data_persist = True
        
    def is_persisted(self):
        
        return self.data_persist

    def get_persisted_data_dim_as_str(self):

        if self.has_value():
            return self.value_holder.get_persisted_data_dim_as_str()
        else:
            return ''

    def get(self):

        # this is to support the multi-graph paradigm
        self.remove_dead_child_nodes()
        
        if self.value_holder.has_value():

            # update graph_dict 
            # during a computation execution, the value_holder can hold transient data
            # so we need to check that this data node is indeed persisted
            # as well as actually has data
            if self.is_persisted():
                if self.verbose:
                    print('persisted', self.node_uid)

                data_dim = self.get_persisted_data_dim_as_str()
                self.graph_dict[self.node_uid]['data_dim'] = data_dim

            return self.value_holder.get()
        else:
            if self.verbose:
                print('computing for {}'.format(self.node_uid))
            
            self.activate_dependency_op_nodes()
            self.parent_node_weak_refs[0]().run()

            # update graph_dict
            if self.is_persisted():
                if self.verbose:
                    print('persisted', self.node_uid)

                data_dim = self.get_persisted_data_dim_as_str()
                self.graph_dict[self.node_uid]['data_dim'] = data_dim

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

        self.graph_dict[self.node_uid]['data_dim'] = ''
        
        del self.value_holder
        self.value_holder = DataHolderNode(self.graph_uid, self.graph_alias, self.node_uid, None, self.verbose)
        