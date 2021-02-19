from .base_node import BaseNode
from .data_holder_node import DataHolderNode

from ..utils import view_full
from ..utils import view_summary

import warnings
import copy
from IPython.display import display

class DataNode(BaseNode):
    
    def __init__(self, graph_uid, graph_alias, node_uid, value="__specialPFV__NoneData", persist=False, verbose=False, alias=None, graph_dict=None):
        super(DataNode, self).__init__(graph_uid, graph_alias, node_uid, 'data', verbose, alias or 'data')
        
        self.value_holder = DataHolderNode(graph_uid, graph_alias, self.node_uid, value, self.verbose)

        self.data_persist = persist
        self.graph_uid = graph_uid
        self.graph_alias = graph_alias

        self.graph_dict = graph_dict

        self.shallow_persist = False
        self.is_active = False

    def set_value(self, value):
        
        self.value_holder.set_value(value)
        
    def has_value(self):
        
        return self.value_holder.has_value()

    def persist(self):

        self.data_persist = True

    def shallowly_persist(self):

        self.shallow_persist = True
        
    def is_persisted(self):
        
        return self.data_persist

    def is_shallowly_persisted(self):

        return self.shallow_persist

    def get_persisted_data_dim_as_str(self):

        if self.has_value():
            return self.value_holder.get_persisted_data_dim_as_str()
        else:
            return ''

    def view_activated(self, summary):

        dependency_ancestor_node_weak_refs = self.get_all_dependency_ancestor_node_weak_refs()
        dependency_ancestor_node_uids = [elem().node_uid for elem in dependency_ancestor_node_weak_refs]

        dependency_ancestor_node_uids += [self.node_uid]

        graph_dict_copied = copy.deepcopy(self.graph_dict)

        for dependency_ancestor_node_uid in dependency_ancestor_node_uids:
            
            graph_dict_copied[dependency_ancestor_node_uid]['is_activated'] = True

        _graph_attributes = {'data_node_fontsize': '10',
                             'data_node_shape': 'box',
                             'data_node_color': 'None',
                             'op_node_fontsize': '12',
                             'op_node_shape': 'box',
                             'op_node_color': 'white',
                             'graph_ranksep': '0.415',
                             'graph_node_fontsize': '12.85',
                             'graph_node_shape': 'box3d',
                             'graph_node_color': 'white',
                             'graph_node_shapesize': '0.574',
                             'persist_record_shape': 'True'}

        if summary :
            display(view_summary(graph_dict_copied, _graph_attributes, verbose=self.verbose, current_graph_uid=self.graph_uid))
        else:
            display(view_full(graph_dict_copied, _graph_attributes, verbose=self.verbose, current_graph_uid=self.graph_uid))

    def get(self, view=False, summary=True):

        # this is to support the multi-graph paradigm
        self.remove_dead_child_nodes()
        
        if self.value_holder.has_value():

            if view:
                self.view_activated(summary)
                
            if self.verbose:
                if self.is_shallowly_persisted():
                    print('{} has been shallowly persisted'.format(self.node_uid))
                elif self.is_persisted():
                    print('{} has been persisted'.format(self.node_uid))
                elif self.has_value():
                    print('{} has been computed'.format(self.node_uid))


            # update graph_dict 
            # during a computation execution, the value_holder can hold transient data
            # so we need to check that this data node is indeed persisted
            # as well as actually has data
            if self.is_persisted():
                data_dim = self.get_persisted_data_dim_as_str()
                self.graph_dict[self.node_uid]['data_dim'] = data_dim

            return self.value_holder.get()

        else:

            self.activate_dependency_op_nodes()
            
            if view:

                self.view_activated(summary)

            if self.verbose:
                print('computing for {}'.format(self.node_uid))

            self.parent_node_weak_refs[0]().run()  # a data node can only have 1 op parent node

            # update graph_dict
            if self.is_persisted():
                data_dim = self.get_persisted_data_dim_as_str()
                self.graph_dict[self.node_uid]['data_dim'] = data_dim

            return self.value_holder.get()

    def activate_dependency_op_nodes(self):
        
        dependency_ancestor_node_weak_refs = self.get_dependency_ancestor_node_weak_refs()
        dependency_op_nodes_weak_refs = [elem for elem in dependency_ancestor_node_weak_refs 
                                  if elem().node_type == 'operation']
        
        for dependency_op_node_weak_ref in dependency_op_nodes_weak_refs:
            dependency_op_node_weak_ref().activate()

    def release_memory(self):
        
        if self.is_persisted():
            warnings.warn("You are releasing a DataNode that was persisted!", RuntimeWarning)

        self.graph_dict[self.node_uid]['data_dim'] = ''
        
        del self.value_holder

        self.value_holder = DataHolderNode(self.graph_uid, self.graph_alias, self.node_uid, "__specialPFV__NoneData", self.verbose)
        