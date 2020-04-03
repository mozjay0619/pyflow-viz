from .node import DataNode
from .node import OperationNode
from .utils import ExtendedRef
from .utils import view_full
from .utils import view_summary
from .utils import save_graph_image
from .utils import contains_return_statement

from collections import defaultdict
from collections import Iterable
import sys
import copy

MAX_INTEGER = sys.maxsize  # for python3 only need sys.maxint for python2

class GraphBuilder():
    
    def __init__(self, persist=False, verbose=False):
        
        self.persist = persist
        self.verbose = verbose
        
        self.node_count = -1
        self.strong_ref_dict = {}
        self.graph_dict = defaultdict(dict)

        self.default_graph_attributes = {
            'data_node_fontsize': 11, 
            'data_node_shape': 'box',
            'data_node_color': None,
            'op_node_fontsize': 12,
            'op_node_shape': 'ellipse',
            'op_node_color': 'white',
            'graph_ranksep': 0.475
        }
        self.user_defined_graph_attributes = None
    
    def add(self, func, method_alias=None, output_alias=None, n_out=1, persist=False, rank=None, color=None, shape=None, fontsize=None):
        
        self.func = func
        self.method_alias = method_alias
        self.output_alias = output_alias

        self.n_out = n_out
        self.func_persist = persist

        if ( not isinstance(self.output_alias, list) and not isinstance(self.output_alias, tuple) ):
            self.output_alias = [self.output_alias]
        if not output_alias:
            self.output_alias *= n_out
        
        if rank is None:
            self.rank = MAX_INTEGER
        else:
            self.rank = rank

        self.color = color
        self.shape = shape
        self.fontsize = fontsize
        
        return self
    
    def __call__(self, *args):

        self.node_count += 1

        if self.method_alias:
            op_node_uid = '{}_{}'.format(self.method_alias, self.node_count)
        else:
            op_node_uid = '{}_{}'.format(self.func.__name__, self.node_count)

        self.strong_ref_dict[op_node_uid] = OperationNode(op_node_uid, self.func, self.n_out, 
                                                          verbose=self.verbose, alias=self.method_alias)
        op_node_weak_ref = ExtendedRef(self.strong_ref_dict[op_node_uid])
        
        node_graph_attributes_dict = {'rank': self.rank, 
                                      'color': self.color, 
                                      'shape': self.shape,
                                      'fontsize': self.fontsize}
        op_node_properties_dict = {'children': [], 
                                   'parents': [], 
                                   'type': 'operation', 
                                   'alias': op_node_weak_ref().alias,
                                   'uid': op_node_weak_ref().node_uid,
                                   'attributes': node_graph_attributes_dict}
        self.graph_dict[op_node_uid] = op_node_properties_dict
        
        # create edge: op_node --> parent data_nodes
        for i, inp in enumerate(args):
            
            if isinstance(inp, ExtendedRef) and isinstance(inp(), DataNode):
                # this data node already exists in the graph dict
                op_node_weak_ref().parent_node_weak_refs.append(inp)
                op_node_weak_ref().parent_node_weak_refs[i] = inp
                
            else:
                self.node_count += 1
                parent_data_node_uid = 'data_{}'.format(self.node_count)
                # if inp is raw value, we need to persist since we can't re-compute it from graph
                self.strong_ref_dict[parent_data_node_uid] = DataNode(node_uid=parent_data_node_uid, 
                                                                      persist=True, verbose=self.verbose)
                data_node_weak_ref = ExtendedRef(self.strong_ref_dict[parent_data_node_uid])
                
                op_node_weak_ref().parent_node_weak_refs.append(data_node_weak_ref)
                op_node_weak_ref().parent_node_weak_refs[i]().set_value(inp)
                
        # create edge: op_node --> children data_nodes
        for i in range(self.n_out):

            # if the current method has no return statement, we do not want to create a child data node
            if not contains_return_statement(self.func):
                continue
            
            self.node_count += 1

            if self.output_alias[0]:
                child_data_node_uid = '{}_{}'.format(self.output_alias[i], self.node_count)
            else:
                child_data_node_uid = 'data_{}'.format(self.node_count)

            persist_this_node = self.persist or self.func_persist
            self.strong_ref_dict[child_data_node_uid] = DataNode(node_uid=child_data_node_uid, 
                                                                 verbose=self.verbose, persist=persist_this_node, alias=self.output_alias[i])
            data_node_weak_ref = ExtendedRef(self.strong_ref_dict[child_data_node_uid])
            op_node_weak_ref().child_node_weak_refs.append(data_node_weak_ref)
            
            self.graph_dict[op_node_uid]['children'].append(child_data_node_uid)
            
        # create edge: parent_data_nodes --> op_node
        for parent_data_node_weak_ref in op_node_weak_ref().parent_node_weak_refs:
            
            parent_data_node_weak_ref().child_node_weak_refs.append(op_node_weak_ref)
            parent_data_node_uid = parent_data_node_weak_ref().node_uid
            if parent_data_node_uid in self.graph_dict:
                self.graph_dict[parent_data_node_uid]['children'].append(op_node_weak_ref().node_uid)
            else:
                node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                              'color': None, 
                                              'shape': None,
                                              'fontsize': self.fontsize}
                node_properties_dict = {'children': [op_node_weak_ref().node_uid], 
                                        'parents': [], 
                                        'type': 'data',
                                        'alias': parent_data_node_weak_ref().alias,
                                        'uid': parent_data_node_weak_ref().node_uid,
                                        'attributes': node_graph_attributes_dict}
                self.graph_dict[parent_data_node_uid] = node_properties_dict
                
            self.graph_dict[op_node_uid]['parents'].append(parent_data_node_uid)
        
        # create edge: children_data_nodes --> op_node
        for child_data_node_weak_ref in op_node_weak_ref().child_node_weak_refs:
            
            child_data_node_weak_ref().parent_node_weak_refs.append(op_node_weak_ref)
            child_data_node_uid = child_data_node_weak_ref().node_uid
            if child_data_node_uid in self.graph_dict:
                self.graph_dict[parent_data_node_uid]['parents'].append(op_node_weak_ref().node_uid)
            else:
                node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                              'color': None, 
                                              'shape': None,
                                              'fontsize': self.fontsize}
                node_properties_dict = {'children': [], 
                                        'parents': [op_node_weak_ref().node_uid], 
                                        'type': 'data', 
                                        'alias': child_data_node_weak_ref().alias,
                                        'uid': child_data_node_weak_ref().node_uid,
                                        'attributes': node_graph_attributes_dict}
                self.graph_dict[child_data_node_uid] = node_properties_dict
                
        if self.n_out > 1:
            return op_node_weak_ref().child_node_weak_refs
        else:
            if len(op_node_weak_ref().child_node_weak_refs) == 0:
                return None
            else:
                return op_node_weak_ref().child_node_weak_refs[0]

    def run(self, *args):    

        requested_data_node_uids = [elem().node_uid for elem in args]
        
        requested_data_nodes = [(k, v) for k, v in self.strong_ref_dict.items() 
                                     if v.node_uid in requested_data_node_uids]
        
        for k, v in requested_data_nodes:
            v.persist()
        
        op_nodes = [(k, v) for k, v in self.strong_ref_dict.items() if v.node_type == 'operation']

        for k, v in op_nodes:
            v.activate()
        
        for k, v in op_nodes:
            v.run()
        
        return args

    def remove(self, n=1):

        op_nodes = [(k, v) for k, v in self.strong_ref_dict.items() if v.node_type == 'operation']
        rev_op_nodes = op_nodes[::-1]
        rev_op_nodes = rev_op_nodes[:n]

        for k, v in rev_op_nodes:

            # first get all the children nodes of the op node
            child_data_node_uids = self.graph_dict[k]['children']
            
            # remove the child data nodes 
            # no need to unlink them from its parent op node since
            # all data node has only one parent op node (i.e. k)
            for child_data_node_uid in child_data_node_uids:
                
                # remove from graph dict
                self.graph_dict.pop(child_data_node_uid)
                
                # remove the strong reference from memory
                del self.strong_ref_dict[child_data_node_uid]

                self.node_count -= 1
            
            # get all the parent data nodes of the op node
            parent_data_node_uids = self.graph_dict[k]['parents']
            
            # unlink the current op node (i.e. k) from its parent 
            # data nodes
            for parent_data_node_uid in parent_data_node_uids:
                
                # if the parent data node is raw input, remove it
                if len(self.graph_dict[parent_data_node_uid]['parents']) == 0:
                    
                    # remove from graph dict
                    self.graph_dict.pop(parent_data_node_uid)
                    
                    # emove the strong reference from memory
                    del self.strong_ref_dict[parent_data_node_uid]

                    self.node_count -= 1
                    
                    continue
                    
                # unlink from parent data node in graph dict
                old_child_node_uids = self.graph_dict[parent_data_node_uid]['children']
                new_child_node_uids = [elem for elem in old_child_node_uids if elem != k]
                self.graph_dict[parent_data_node_uid]['children'] = new_child_node_uids
                
                # unlink from parent data node in memory
                self.strong_ref_dict[parent_data_node_uid].remove_child_node(self.strong_ref_dict[parent_data_node_uid])
                self.strong_ref_dict[parent_data_node_uid].remove_child_node(v)
                
            # remove the op node from graph dict
            self.graph_dict.pop(k)
            
            # remove the strong reference to it
            del self.strong_ref_dict[k]

            self.node_count -= 1
            
    @property
    def graph_attributes(self):

        if self.user_defined_graph_attributes:
            graph_attributes = copy.copy(self.default_graph_attributes)
            graph_attributes.update(self.user_defined_graph_attributes)
        else:
            graph_attributes = copy.copy(self.default_graph_attributes)

        return graph_attributes

    def _graph_attributes(self):

        return {k: str(v) for k, v in self.graph_attributes.items()}

    def view(self, summary=True, graph_attributes=None):

        if graph_attributes:  # need validity check here
            self.user_defined_graph_attributes = graph_attributes
        
        if summary:
            return view_summary(self.graph_dict, self._graph_attributes(), verbose=self.verbose)
        else:
            return view_full(self.graph_dict, self._graph_attributes(), verbose=self.verbose)

    def save_view(self, summary=True, graph_attributes=None, dirpath=None, filename='digraph', fileformat='png'):

        if fileformat not in ['pdf', 'png']:
            raise TypeError("Expected fileformat to be 'pdf' or 'png', but instead "
                            "got {}".format(fileformat))

        graph = self.view(summary, graph_attributes)
        img_filepath = save_graph_image(graph, dirpath, filename, fileformat)
        return img_filepath


