from .node import DataNode
from .node import OperationNode
from .utils import ExtendedRef
from .utils import view_full
from .utils import view_summary
from .utils import save_graph_image
from .utils import contains_return_statement
from .utils import topological_sort
# from .utils import add_to_module_global_namespace

from collections import defaultdict
from collections import Iterable
import sys
import copy

MAX_INTEGER = sys.maxsize  


class GraphBuilder():
    
    def __init__(self, alias=None, persist=False, verbose=False, inside_pandasUDF=None):#, shared_args=dict()):

        if not (isinstance(alias, str) or alias is None):
            raise TypeError("[ alias ] must be either None or string type")

        if not isinstance(persist, bool):
            raise TypeError("[ persist ] must be bool type")

        if not isinstance(verbose, bool):
            raise TypeError("[ verbose ] must be bool type")

        self.graph_alias = alias or "graph"
        self.graph_uid = "{}_{}".format(self.graph_alias, id(self))

        self.persist = persist
        self.verbose = verbose
        
        self.node_count = 0
        self.strong_ref_dict = {}
        self.graph_dict = defaultdict(dict)

        self.default_graph_attributes = {
            'data_node_fontsize': 10, 
            'data_node_shape': 'box',
            'data_node_color': None,
            'op_node_fontsize': 12,
            'op_node_shape': 'box',
            'op_node_color': 'white',
            'graph_ranksep': 0.415,
            'graph_node_fontsize': 12.85,
            'graph_node_shape': 'box3d',
            'graph_node_color': 'white',
            'graph_node_shapesize': 0.574,
            'persist_record_shape': True
        }
        self.user_defined_graph_attributes = None

        self.inside_pandasUDF = inside_pandasUDF

        # if not isinstance(shared_args, dict):
        #     raise TypeError("shared_args must be a dictionary. Instead received {}".format(shared_args))
        # self.shared_args = shared_args
    
    def add(self, func, method_alias=None, output_alias=None, n_out=1, persist=False, rank=None, color=None, shape=None, fontsize=None):

        # add_to_module_global_namespace(func, self.shared_args)
        
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

        # Create/update the graph using doubly linked list data structure

        op_node_uid = '{}_{}'.format(self.method_alias or self.func.__name__, self.node_count)

        # create op node to hold the input function method
        self.strong_ref_dict[op_node_uid] = OperationNode(
            graph_uid=self.graph_uid, 
            graph_alias=self.graph_alias, 
            node_uid=op_node_uid, 
            function=self.func, 
            n_out=self.n_out, 
            verbose=self.verbose, 
            alias=self.method_alias,
            graph_dict=self.graph_dict)
        op_node_weak_ref = ExtendedRef(self.strong_ref_dict[op_node_uid])
        self.node_count += 1  

        # create edge: parent data_nodes <--> op_node
        for i, inp in enumerate(args):
            
            # if the inp is actually another node:
            if isinstance(inp, ExtendedRef) and isinstance(inp(), DataNode):

                # inp is already (a weak reference to) a data node

                # add the weak ref to the parent data node to the op node's references
                op_node_weak_ref().parent_node_weak_refs.append(inp)  

                # add the weak reference of the current op node to the parent data node's references 
                inp().child_node_weak_refs.append(op_node_weak_ref)

            # if the inp is raw data, and not another data node
            else:

                parent_data_node_uid = 'data_{}'.format(self.node_count)  # raw data has no alias

                # if inp is raw value, we need to persist since we can't re-compute it from graph
                # create a new data node to hold this raw data
                persist_this_node = True

                # define a new data node that will hold the raw input data
                self.strong_ref_dict[parent_data_node_uid] = DataNode(
                    graph_uid=self.graph_uid, 
                    graph_alias=self.graph_alias, 
                    node_uid=parent_data_node_uid, 
                    persist=persist_this_node, 
                    verbose=self.verbose,
                    graph_dict=self.graph_dict)
                data_node_weak_ref = ExtendedRef(self.strong_ref_dict[parent_data_node_uid])
                self.node_count += 1

                # set the value of the new data node with the input inp value
                data_node_weak_ref().set_value(inp)
                
                # add the weak ref to the parent data node (newly created) to the op node's references
                op_node_weak_ref().parent_node_weak_refs.append(data_node_weak_ref)

                # add the weak reference of the current op node to the parent data node's references 
                data_node_weak_ref().child_node_weak_refs.append(op_node_weak_ref)

        # create edge: op_node <--> n_out children data_node(s) 
        for i in range(self.n_out):

            # if the current method has no return statement, we do not want to create a child data node
            if not (self.inside_pandasUDF or contains_return_statement(self.func)):
                continue

            child_data_node_uid = '{}_{}'.format(self.output_alias[i] or 'data', self.node_count)

            persist_this_node = self.persist or self.func_persist

            # define a new data node that will hold the result of the current op_node's computations
            self.strong_ref_dict[child_data_node_uid] = DataNode(
                graph_uid=self.graph_uid, 
                graph_alias=self.graph_alias,
                node_uid=child_data_node_uid, 
                verbose=self.verbose, 
                persist=persist_this_node, 
                alias=self.output_alias[i],
                graph_dict=self.graph_dict)
            data_node_weak_ref = ExtendedRef(self.strong_ref_dict[child_data_node_uid])
            self.node_count += 1  

            # give the (weak) reference of the above children data_node to the op_node so that
            # the current op_node points to the data_node
            op_node_weak_ref().child_node_weak_refs.append(data_node_weak_ref)

            # add the weak reference of the current op node to the child data node's references
            data_node_weak_ref().parent_node_weak_refs.append(op_node_weak_ref)

        # Create/update the graph_dict for visualization

        # define the graph visualization attributes of the current op node
        node_graph_attributes_dict = {'rank': self.rank, 
                                      'color': self.color, 
                                      'shape': self.shape,
                                      'fontsize': self.fontsize,
                                      'shapesize': None}

        method_attributes_dict = {'name': self.func.__name__, 
                                  'doc_string': self.func.__doc__}

        op_node_properties_dict = {'children': [], 
                                   'parents': [], 
                                   'type': 'operation', 
                                   'is_persisted': False,
                                   'data_dim': '',
                                   'alias': op_node_weak_ref().alias,
                                   'node_uid': op_node_weak_ref().node_uid,
                                   'graph_alias': self.graph_alias,
                                   'graph_uid': op_node_weak_ref().graph_uid,
                                   'attributes': node_graph_attributes_dict,
                                   'method_attributes': method_attributes_dict}

        # add the op node visualization attributes to the graph_dict
        self.graph_dict[op_node_uid] = op_node_properties_dict

        # create edge: op_node <--> parent data_nodes
        for parent_data_node_weak_ref in op_node_weak_ref().parent_node_weak_refs:

            # if the parent data node comes from a different graph
            # the second condition is there to prevent detached op node when the previous
            # graph result is used in more than 1 place.
            if parent_data_node_weak_ref().graph_uid != self.graph_uid:

                _ext_node_uid = "{} from {}".format(
                    parent_data_node_weak_ref().node_uid, 
                    parent_data_node_weak_ref().graph_uid)

                if _ext_node_uid not in self.graph_dict:

                    node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                                  'color': "red", 
                                                  'shape': None,
                                                  'fontsize': self.fontsize,
                                                  'shapesize': None}

                    node_properties_dict = {'children': [], 
                                            'parents': [],  
                                            'type': 'data',
                                            'is_persisted': parent_data_node_weak_ref().is_persisted(),
                                            'data_dim': parent_data_node_weak_ref().get_persisted_data_dim_as_str(),
                                            'alias': parent_data_node_weak_ref().alias,
                                            'node_uid': _ext_node_uid,
                                            'graph_alias': parent_data_node_weak_ref().graph_alias,
                                            'graph_uid': parent_data_node_weak_ref().graph_uid,
                                            'attributes': node_graph_attributes_dict}

                    # add the parent data node visualization attributes to the graph_dict
                    self.graph_dict[_ext_node_uid] = node_properties_dict

                # make the parent data node point to the op node
                self.graph_dict[_ext_node_uid]['children'].append(op_node_weak_ref().node_uid)

                # make the op node point to the parent data node
                self.graph_dict[op_node_weak_ref().node_uid]['parents'].append(_ext_node_uid)

                continue

            # if the parent data node is not already part of the graph_dict
            elif parent_data_node_weak_ref().node_uid not in self.graph_dict:

                node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                              'color': None, 
                                              'shape': None,
                                              'fontsize': self.fontsize,
                                              'shapesize': None}

                if parent_data_node_weak_ref().has_value():
                    data_dim = parent_data_node_weak_ref().get_persisted_data_dim_as_str()
                else:
                    data_dim = ''

                node_properties_dict = {'children': [], 
                                        'parents': [], 
                                        'type': 'data',
                                        'is_persisted': parent_data_node_weak_ref().is_persisted(),
                                        'data_dim': data_dim,
                                        'alias': parent_data_node_weak_ref().alias,
                                        'node_uid': parent_data_node_weak_ref().node_uid,
                                        'graph_alias': self.graph_alias,
                                        'graph_uid': self.graph_uid,
                                        'attributes': node_graph_attributes_dict}

                # add the parent data node visualization attributes to the graph_dict
                self.graph_dict[parent_data_node_weak_ref().node_uid] = node_properties_dict

            # make the parent data node point to the op node
            self.graph_dict[parent_data_node_weak_ref().node_uid]['children'].append(op_node_weak_ref().node_uid)

            # make the op node point to the parent data node
            self.graph_dict[op_node_weak_ref().node_uid]['parents'].append(parent_data_node_weak_ref().node_uid)

        # create edge: op_node <--> n_out children data_node(s)
        for child_data_node_weak_ref in op_node_weak_ref().child_node_weak_refs:

            # if the child data node is not already part of the graph_dict
            if child_data_node_weak_ref().node_uid not in self.graph_dict:

                node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                              'color': None, 
                                              'shape': None,
                                              'fontsize': self.fontsize,
                                              'shapesize': None}

                node_properties_dict = {'children': [], 
                                        'parents': [], 
                                        'type': 'data', 
                                        'is_persisted': child_data_node_weak_ref().is_persisted(),
                                        'data_dim': '',
                                        'alias': child_data_node_weak_ref().alias,
                                        'node_uid': child_data_node_weak_ref().node_uid,
                                        'graph_alias': self.graph_alias,
                                        'graph_uid': self.graph_uid,
                                        'attributes': node_graph_attributes_dict}

                # add the child data node visualization attributes to the graph_dict
                self.graph_dict[child_data_node_weak_ref().node_uid] = node_properties_dict

            # make the child data node point to the op node
            self.graph_dict[child_data_node_weak_ref().node_uid]['parents'].append(op_node_weak_ref().node_uid)

            # make the op node point to the child data node
            self.graph_dict[op_node_weak_ref().node_uid]['children'].append(child_data_node_weak_ref().node_uid)
                
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

        # because op node calls get only on the parent data node, 
        # and directly assigns the current function result to child node
        # invoke get() on the last op node's child data node to make sure the 
        # necessary persistance occurs.
        for child_data_node_weak_ref in v.child_node_weak_refs:
            child_data_node_weak_ref().get()
        
        if len(args) == 1:
            return args[0].get()
        else:
            return [arg.get() for arg in args]

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
                    
                    # remove the strong reference from memory
                    # if the parent data node was from a different graph, 
                    # we don't want to release its memory
                    if parent_data_node_uid in self.strong_ref_dict:
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

    def update_graph_attributes(self, graph_attributes):

        self.user_defined_graph_attributes = graph_attributes

    def preprocess_graph_dict(self):
        """
        1. support for multi graph
        - need to create a copy of graph dict so that we can give it an appendage of graph node
        """
        graph_dict = copy.deepcopy(self.graph_dict)
        external_graphs_dict = {k: v for k, v in graph_dict.items() if v['graph_uid']!=self.graph_uid}

        for k, v in external_graphs_dict.items():

            node_graph_attributes_dict = {'rank': MAX_INTEGER, 
                                          'color': self.graph_attributes['graph_node_color'], 
                                          'shape': self.graph_attributes['graph_node_shape'],
                                          'fontsize': self.graph_attributes['graph_node_fontsize'],
                                          'shapesize': self.graph_attributes['graph_node_shapesize']}

            op_node_properties_dict = {'children': [k], 
                                       'parents': [], 
                                       'type': 'operation', 
                                       'alias': v['graph_alias'],
                                       'node_uid': k + "_ghost",
                                       'graph_alias': v['graph_alias'],
                                       'graph_uid': v['graph_uid'],
                                       'attributes': node_graph_attributes_dict}

            v['parents'].append(k+"_ghost")
            graph_dict[k+"_ghost"] = op_node_properties_dict

        sorted_graph_dict = topological_sort(graph_dict)
        return sorted_graph_dict

    def view(self, summary=True, graph_attributes=None):

        if graph_attributes:  # need validity check here
            self.update_graph_attributes(graph_attributes)

        preprocessed_graph_dict = self.preprocess_graph_dict()
        
        if summary:
            return view_summary(preprocessed_graph_dict, self._graph_attributes(), verbose=self.verbose, current_graph_uid=self.graph_uid)
        else:
            return view_full(preprocessed_graph_dict, self._graph_attributes(), verbose=self.verbose, current_graph_uid=self.graph_uid)

    def save_view(self, summary=True, graph_attributes=None, dirpath=None, filename='digraph', fileformat='png'):

        if fileformat not in ['pdf', 'png']:
            raise TypeError("Expected fileformat to be 'pdf' or 'png', but instead "
                            "got {}".format(fileformat))

        graph = self.view(summary, graph_attributes)
        img_filepath = save_graph_image(graph, dirpath, filename, fileformat)
        return img_filepath
