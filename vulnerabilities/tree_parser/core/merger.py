import copy
from typing import List, Dict, Any
from interfaces.TreeMerger import TreeMergerInterface

class TreeMergerImpl(TreeMergerInterface):
    def merge_trees(self, trees: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trees:
            return {'name': '.', 'type': 'directory', 'children': []}
        
        root = {'name': '.', 'type': 'directory', 'children': []}
        
        def add_node(parent_node: Dict[str, Any], new_node: Dict[str, Any]):
            existing_child = None
            for child in parent_node.get('children', []):
                if child['name'] == new_node['name']:
                    existing_child = child
                    break
            
            if existing_child:
                for child_in_new_node in new_node.get('children', []):
                    add_node(existing_child, child_in_new_node)
            else:
                new_child_copy = copy.deepcopy(new_node)
                if 'children' not in parent_node:
                    parent_node['children'] = []
                parent_node['children'].append(new_child_copy)

        for tree in trees:
            add_node(root, tree)
            
        root['children'].sort(key=lambda x: x['name'])
        return root
