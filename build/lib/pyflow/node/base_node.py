class BaseNode(object):
    
    def __init__(self, node_uid, node_type, verbose, alias=None, *args, **kwargs):
        
        self.node_uid = node_uid
        self.alias = alias
        
        if node_type not in ['data', 'operation', 'data_holder']:
            raise ValueError("Expected 'data' or 'operation', "
                             "instead got '{}'".format(node_type))
        
        self.node_type = node_type
        self.verbose = verbose
        
        self.parent_node_weak_refs = []
        self.child_node_weak_refs = []
        
    def has_parent_node_weak_refs(self):

        return len(self.parent_node_weak_refs) > 0
    
    def get_parent_node_weak_refs(self):

        return self.parent_node_weak_refs
        
    def get_child_node_weak_refs(self):

        return self.child_node_weak_refs
    
    def get_node_uid(self):

        return self.node_uid
    
    def get_ancestor_node_weak_refs(self):

        ancestors_weak_refs = list()
        DataNode._get_ancestor_node_weak_refs(self, ancestors_weak_refs)
        return ancestors_weak_refs
    
    @staticmethod
    def _get_ancestor_node_weak_refs(self, acc):
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
                BaseNode._get_ancestor_node_weak_refs(parent_node_weak_ref(), acc)

            else:

                acc.append(parent_node_weak_ref)

    def get_descendant_node_weak_refs(self):

        pass
    
    def __del__(self):

        if self.verbose:
            print("{} destroyed!".format(self.node_uid))
    
    