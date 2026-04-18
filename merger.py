import json
import copy
from typing import List, Dict, Any

def merge_trees(trees: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple trees into a single aggregated tree.
    
    Args:
        trees: List of tree dictionaries
    
    Returns:
        Merged tree structure
    """
    if not trees:
        return {'name': '.', 'type': 'directory', 'children': []}
    
    # A root node to aggregate everything
    root = {'name': '.', 'type': 'directory', 'children': []}
    
    def add_node(parent_node: Dict[str, Any], new_node: Dict[str, Any]):
        # Find if a node with the same name exists in parent_node's children
        existing_child = None
        for child in parent_node.get('children', []):
            if child['name'] == new_node['name']:
                existing_child = child
                break
        
        if existing_child:
            # If exists, recursively merge the children
            for child_in_new_node in new_node.get('children', []):
                add_node(existing_child, child_in_new_node)
        else:
            # If not, add the new node (using a copy to avoid mutating input)
            new_child_copy = copy.deepcopy(new_node)
            if 'children' not in parent_node:
                parent_node['children'] = []
            parent_node['children'].append(new_child_copy)

    for tree in trees:
        # We merge the top-level children of each tree into our global root
        for top_level_child in tree.get('children', []):
            add_node(root, top_level_child)
            
    # Sort by name for consistent ordering
    root['children'].sort(key=lambda x: x['name'])
    
    return root
