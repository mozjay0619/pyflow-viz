import weakref
import copy
import os
import ast
import inspect
import textwrap

from graphviz import Digraph

class ExtendedRef(weakref.ref):

    def get(self):
        return self().get()
    
    def get_node_uid(self):
        return self().get_node_uid()
    
    def release_memory(self):
        return self().release_memory()

    def has_value(self):
        return self().has_value()
    
def contains_return_statement(func):
    func = textwrap.dedent(inspect.getsource(func))
    func_source_tree = ast.walk(ast.parse(func))
    return any(isinstance(node, ast.Return) for node in func_source_tree)

def get_rank(node_properties_dict):
    node_graph_attributes_dict = node_properties_dict['attributes']
    rank = node_graph_attributes_dict['rank']
    return rank

def get_type(node_properties_dict):
    node_type = node_properties_dict['type']
    return node_type

def view_full(graph_dict, graph_attributes, verbose):
    
    ranks = set()

    for node_properties_dict in graph_dict.values():
        
        rank = get_rank(node_properties_dict)
        if rank is not None:
            ranks.add(rank)

    ranks = list(ranks)
    ranks.sort()
    
    subgraphs = []

    for rank in ranks:
        subgraph = {k: v for k, v in graph_dict.items() if rank == get_rank(v)}
        subgraphs.append(subgraph)
        
    ranked_subgraphs = subgraphs[0:-1]
    unranked_subgraph = subgraphs[-1]

    graph = Digraph()
    graph.attr(splines='true', overlap='false', ranksep=graph_attributes['graph_ranksep'])

    for ranked_subgraph in ranked_subgraphs:

        with graph.subgraph() as subg:

            subg.attr(rank='same')

            for k, v in ranked_subgraph.items():

                if v['type'] != 'operation':
                    continue

                label = v['node_uid'] if verbose else v['alias']
                if v['attributes']['shape'] is not None:
                    shape = v['attributes']['shape']
                else:
                    shape = graph_attributes['op_node_shape']

                if v['attributes']['color'] is not None:
                    color = v['attributes']['color']
                else:
                    color = graph_attributes['op_node_color']
                    
                subg.node(
                    k, 
                    label=label, 
                    shape=shape, 
                    fontsize=graph_attributes['op_node_fontsize'], 
                    height='0.0', width='0.0', fillcolor=color, style='filled')

                for child in v['children']:
                    label = graph_dict[child]['node_uid'] if verbose else graph_dict[child]['alias']
                    graph.node(
                        child, 
                        label=label,
                        shape=graph_attributes['data_node_shape'], 
                        fontsize=graph_attributes['data_node_fontsize'], 
                        height='0.0', width='0.0')
                    graph.edge(k, child)

                for parent in v['parents']:
                    label = graph_dict[parent]['node_uid'] if verbose else graph_dict[parent]['alias']
                    graph.node(
                        parent, 
                        label=label,
                        shape=graph_attributes['data_node_shape'], 
                        fontsize=graph_attributes['data_node_fontsize'], 
                        height='0.0', width='0.0')
                    graph.edge(parent, k)

    for k, v in unranked_subgraph.items():

        if v['type'] != 'operation':
            continue
        
        label = v['node_uid'] if verbose else v['alias']

        if v['attributes']['shape'] is not None:
            shape = str(v['attributes']['shape'])
        else:
            shape = graph_attributes['op_node_shape']

        if v['attributes']['color'] is not None:
            color = str(v['attributes']['color'])
        else:
            color = graph_attributes['op_node_color']

        if v['attributes']['fontsize'] is not None:
            fontsize = str(v['attributes']['fontsize'])
        else:
            fontsize = graph_attributes['op_node_fontsize']

        if v['attributes']['shapesize'] is not None:
            shapesize = str(v['attributes']['shapesize'])
        else:
            shapesize = '0.0'

        graph.node(
            k, 
            label=label, 
            shape=shape, 
            fontsize=fontsize, 
            height=shapesize, width=shapesize, fillcolor=color, style='filled')

        for child in v['children']:
            label = graph_dict[child]['node_uid'] if verbose else graph_dict[child]['alias']
            graph.node(
                child,
                label=label,
                shape=graph_attributes['data_node_shape'], 
                fontsize=graph_attributes['data_node_fontsize'], 
                height='0.0', width='0.0', fillcolor=color)
            graph.edge(k, child)

        for parent in v['parents']:
            label = graph_dict[parent]['node_uid'] if verbose else graph_dict[parent]['alias']

            graph.node(
                parent, 
                label=label,
                shape=graph_attributes['data_node_shape'], 
                fontsize=graph_attributes['data_node_fontsize'], 
                height='0.0', width='0.0', fillcolor=color)
            graph.edge(parent, k)

    return graph

def view_summary(graph_dict, graph_attributes, verbose):
    
    op_subgraphs = {k: v for k, v in graph_dict.items() if 'operation' == v['type']}
    data_subgraphs = {k: v for k, v in graph_dict.items() if 'data' == v['type']}

    op_graph_dict = copy.deepcopy(op_subgraphs)

    for k, v in op_graph_dict.items():
        v['children'] = []
        v['parents'] = []

    for k, v in op_subgraphs.items():

        for child_data_node_uid in v['children']:

            data_node_prop_dict = data_subgraphs[child_data_node_uid]

            for child_op_node_uid in data_node_prop_dict['children']:

                if child_op_node_uid is not None:

                    op_graph_dict[k]['children'].append(child_op_node_uid)

    return view_full(op_graph_dict, graph_attributes, verbose)

def save_graph_image(graph, dirpath=None, filename=None, fileformat=None):
    
    graph.format = 'png' or fileformat
    try:
        dirpath = os.getcwd() or dirpath
        filename = 'digraph' or filename
        filename = filename
        graph.view(filename=filename, directory=dirpath)
    except FileNotFoundError:
        pass
    finally:
        img_filepath = os.path.join(dirpath, filename + '.' + graph.format)
        dot_filepath = os.path.join(dirpath, filename)
        if not os.path.exists(img_filepath):
            raise FileNotFoundError('{} image file not found!'.format(img_filepath))
        if os.path.exists(dot_filepath):
            os.remove(dot_filepath)
    
    return img_filepath
    
def _recursive_topological_sort(node_uid, graph_dict, stack, visited_flags):
    
    # we have visited this node
    visited_flags[node_uid] = True
    
    for child_node_uid in graph_dict[node_uid]['children']:
        if not visited_flags[child_node_uid]:
            _recursive_topological_sort(child_node_uid, graph_dict, stack, visited_flags)
        
    stack.append(node_uid)
    
def topological_sort(graph_dict):
    
    stack = []
    visited_flags = {k:False for k in graph_dict.keys()}

    for node_uid in graph_dict.keys():
        if not visited_flags[node_uid]:
            _recursive_topological_sort(node_uid, graph_dict, stack, visited_flags)
            
    sorted_graph_dict = {}
    while len(stack)>0:
        node_uid = stack.pop()
        sorted_graph_dict[node_uid] = graph_dict[node_uid]
    
    return sorted_graph_dict
            