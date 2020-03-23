import weakref
import copy
import os

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
    
def get_rank(node_properties_dict):
    node_graph_attributes_dict = node_properties_dict['attributes']
    rank = node_graph_attributes_dict['rank']
    return rank

def get_type(node_properties_dict):
    node_type = node_properties_dict['type']
    return node_type

def view_full(graph_dict, node_default_attributes, verbose):
    
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
    graph.attr(splines='true', overlap='false')

    for ranked_subgraph in ranked_subgraphs:

        with graph.subgraph() as subg:

            subg.attr(rank='same')

            for k, v in ranked_subgraph.items():

                if v['type'] != 'operation':
                    continue

                label = v['uid'] if verbose else v['alias']
                if v['attributes']['shape'] is not None:
                    shape = v['attributes']['shape']
                else:
                    shape = node_default_attributes['op_node_shape']

                if v['attributes']['color'] is not None:
                    color = v['attributes']['color']
                else:
                    color = node_default_attributes['op_node_color']
                    
                subg.node(
                    k, 
                    label=label, 
                    shape=shape, 
                    fontsize=node_default_attributes['op_node_fontsize'], 
                    height='0.0', width='0.0', fillcolor=color, style='filled')

                for child in v['children']:
                    label = graph_dict[child]['uid'] if verbose else graph_dict[child]['alias']
                    graph.node(
                        child, 
                        label=label,
                        shape=node_default_attributes['data_node_shape'], 
                        fontsize=node_default_attributes['data_node_fontsize'], 
                        height='0.0', width='0.0')
                    graph.edge(k, child)

                for parent in v['parents']:
                    label = graph_dict[parent]['uid'] if verbose else graph_dict[parent]['alias']
                    graph.node(
                        parent, 
                        label=label,
                        shape=node_default_attributes['data_node_shape'], 
                        fontsize=node_default_attributes['data_node_fontsize'], 
                        height='0.0', width='0.0')
                    graph.edge(parent, k)

    for k, v in unranked_subgraph.items():

        if v['type'] != 'operation':
            continue
        
        label = v['uid'] if verbose else v['alias']

        if v['attributes']['shape'] is not None:
            shape = v['attributes']['shape']
        else:
            shape = node_default_attributes['op_node_shape']

        if v['attributes']['color'] is not None:
            color = v['attributes']['color']
        else:
            color = node_default_attributes['op_node_color']

        graph.node(
            k, 
            label=label, 
            shape=shape, 
            fontsize=node_default_attributes['op_node_fontsize'], 
            height='0.0', width='0.0', fillcolor=color, style='filled')

        for child in v['children']:
            label = graph_dict[child]['uid'] if verbose else graph_dict[child]['alias']
            graph.node(
                child,
                label=label,
                shape=node_default_attributes['data_node_shape'], 
                fontsize=node_default_attributes['data_node_fontsize'], 
                height='0.0', width='0.0')
            graph.edge(k, child)

        for parent in v['parents']:
            label = graph_dict[parent]['uid'] if verbose else graph_dict[parent]['alias']

            graph.node(
                parent, 
                label=label,
                shape=node_default_attributes['data_node_shape'], 
                fontsize=node_default_attributes['data_node_fontsize'], 
                height='0.0', width='0.0')
            graph.edge(parent, k)

    return graph

def view_summary(graph_dict, node_default_attributes, verbose):
    
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

    return view_full(op_graph_dict, node_default_attributes, verbose)
    
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
    