from typing import List, Dict, Any
import json
from .utils import count_indent, get_node_name
from .merger import merge_trees

def parse_tree_block(lines: List[str]) -> Dict[str, Any]:
    """
    Parse a tree block into a hierarchical structure.
    
    Args:
        lines: List of tree lines
    
    Returns:
        Tree structure dictionary
    """
    lines = [line for line in lines if line.strip()]
    
    if not lines:
        return {'name': '.', 'type': 'directory', 'children': []}
    
    root_name = lines[0].strip()
    root = {'name': root_name, 'str_name': root_name, 'type': 'directory', 'children': []}
    
    current_path = [root_name]
    path_nodes = [root]
    
    for line in lines[1:]:
        depth = count_indent(line)
        node_name = get_node_name(line)
        
        if depth == -1 or not node_name:
            continue
        
        if depth == 0:
            child = {
                'name': node_name,
                'type': 'directory',
                'children': []
            }
            root['children'].append(child)
            current_path = [root_name]
            path_nodes = [root]
        else:
            if depth - 1 < len(path_nodes):
                parent = path_nodes[depth - 1]
                if not parent.get('children'):
                    parent['children'] = []
                
                node = {
                    'name': node_name,
                    'name_str': node_name,
                    'type': 'directory',
                    'children': []
                }
                parent['children'].append(node)
                
                current_path = current_path[:depth + 1]
                current_path.append(node_name)
                path_nodes = path_nodes[:depth + 1]
                path_nodes.append(node)
            else:
                pass
    
    return root


def split_into_trees(input_text: str) -> List[List[str]]:
    """
    Split input text into individual tree blocks.
    """
    lines = input_text.strip().split('\n')
    
    trees = []
    current_block = []
    
    for line in lines:
        line = line
        if not line:
            continue
        
        if line.startswith('/'):
            if current_block:
                trees.append(current_block)
                current_block = []
            current_block = [line]
        else:
            current_block.append(line)
    
    if current_block:
        trees.append(current_block)
    
    return trees


def process_tree_output(input_text: str) -> Dict[str, Any]:
    """
    Process input text and return merged tree as JSON.
    """
    from .formatter import generate_ascii_tree
    
    tree_blocks = split_into_trees(input_text)
    
    tree_dicts = []
    for tree_lines in tree_blocks:
        if tree_lines:
            tree = parse_tree_block(tree_lines)
            tree_dicts.append(tree)
    
    merged_tree = merge_trees(tree_dicts)
    
    json_output = json.dumps(merged_tree, indent=2)
    ascii_output = generate_ascii_tree(merged_tree)
    
    return {
        'tree': merged_tree,
        'json': json_output,
        'ascii': ascii_output
    }


def merge_nix_trees(input_text: str) -> Dict[str, Any]:
    """
    Main function to merge Nix store trees.
    """
    return process_tree_output(input_text)
