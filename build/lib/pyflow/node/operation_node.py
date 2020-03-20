from .base_node import BaseNode

class OperationNode(BaseNode):
    
    def __init__(self, node_uid, function, n_out, verbose=False):
        super(OperationNode, self).__init__(node_uid, 'operation', verbose, function.__name__)
        
        self.function = function
        self.n_out = n_out
        self.is_active = False
    
    def is_activated(self):
        return self.is_active
    
    def activate(self):
        
        if self.is_active:
            return
        
        if self.verbose:
            print('{} activated!'.format(self.node_uid))
            
        self.is_active = True
        
    def deactivate(self):
        
        if not self.is_active:
            return
        
        if self.verbose:
            print('{} deactivated!'.format(self.node_uid))
            
        self.is_active = False
        
    def run(self):
        
        # these strong references will be destroyed once we leave this scope
        parent_data_nodes_values = [parent_data_node_weak_ref().get() 
                                    for parent_data_node_weak_ref 
                                    in self.parent_node_weak_refs]

        if self.verbose:
            print('running {}'.format(self.node_uid))

        output_values = self.function(*parent_data_nodes_values)
        
        if self.n_out > 1:
            for i, output_value in enumerate(output_values):
                self.child_node_weak_refs[i]().set_value(output_value)
        else:
            self.child_node_weak_refs[0]().set_value(output_values)
        
        
        
        # the immediate parent data nodes
        # if any of these are needed by their child op node other than this one, 
        # we don't release them
        for parent_data_node_weak_ref in self.parent_node_weak_refs:
            
            # assume we will need to release this parent data node until proven otherwise
            release_parent_data_node = True
            
            # if the parent node is persisted, no need to check for its children op nodes
            if parent_data_node_weak_ref().is_persisted():
                continue
            
            # checking the child op nodes of the current parent data node
            for child_op_node_weak_ref in parent_data_node_weak_ref().get_child_node_weak_refs():
                
                # if one of the child op node of the parent data node is not activated, 
                # this op node gives us no reason to overturn the prejudice for releasing.
                # also, we do not care about the status of data nodes under this op node
                if not child_op_node_weak_ref().is_activated():
                    continue
                
                # now traversing down to the data nodes of the op node
                # if any of the data nodes are not filled, we need the current data node
                # to feed into that op node, so we do not want to release the memory.
                # having even one such op node + data node is enough reason to persist the 
                # parent data node (from outer most loop)
                for child_output_data_node_weak_ref in child_op_node_weak_ref().get_child_node_weak_refs():
                    
                    # if any child data node value of active op node is missing, we need the current
                    # parent data node to stay persisted
                    if not child_output_data_node_weak_ref().has_value():
                        
                        # for op node with one output data node, this weakref is referring to the
                        # output node it just computed for
                        if self.verbose:
                            print('{} still needed at {}'.format(parent_data_node_weak_ref().get_node_uid(), 
                                                                 child_op_node_weak_ref().get_node_uid()))

                        # at this point, we don't need to check any other child op node of 
                        # this parent data node.
                        # however, we may need to check the next parent_data_node_weak_ref
                        release_parent_data_node = False
                        break
                
                # if we cannot release this parent data node, no need to check other op nodes
                # just go to the next parent data node
                if not release_parent_data_node:
                    break
            
            # if the prejudice for releasing has not been overturned we will release memory
            if release_parent_data_node:
                parent_data_node_weak_ref().release_memory()
                
        self.deactivate()
