#!/usr/bin/env python3
"""
Script to merge Nix store tree outputs and aggregate them into a single tree.

The input format is:
    /nix/store/...
    └───/nix/store/...
        └───/nix/store/...
            └───/nix/store/...

Trees are separated by lines starting with /nix/store (not tree symbols).
"""

import json
import copy
from typing import List, Dict, Any


def count_indent(line: str) -> int:
    """
    Count the indentation level of a tree line.
    
    Each level is represented by 4 characters:
    - │   (vertical bar + 3 spaces)
    
    Returns the number of indentation groups.
    """
    line = line.strip()
    if not line:
        return -1
    
    # Count │ characters at the start (each represents a level)
    count = 0
    i = 0
    while i < len(line) and line[i] == '│':
        count += 1
        i += 4  # Skip │ + 3 spaces
    
    return count


def get_node_name(line: str) -> str:
    """Get the node name from a tree line."""
    line = line.strip()
    if not line:
        return ""
    
    # Find where the name starts (after tree symbols and spaces)
    i = 0
    while i < len(line):
        if line[i] == '│':
            i += 4
        elif line[i] in ['└', '├']:
            i += 4
        elif line[i] == ' ':
            i += 1
        else:
            break
    
    return line[i:].strip()


def parse_tree_block(lines: List[str]) -> Dict[str, Any]:
    """
    Parse a tree block into a hierarchical structure.
    
    Args:
        lines: List of tree lines
    
    Returns:
        Tree structure dictionary
    """
    lines = [line.strip() for line in lines if line.strip()]
    
    if not lines:
        return {'name': '.', 'type': 'directory', 'children': []}
    
    # The first line is the root (we'll use "." as placeholder)
    root_name = lines[0].strip()
    root = {'name': root_name, 'type': 'directory', 'children': []}
    
    # Track nodes in a path structure
    # Each level is tracked by a list
    # We'll build the tree level by level
    
    # Current path: list of node names at each level
    # path[0] = root
    # path[1] = depth 0 nodes (root's children)
    # path[2] = depth 1 nodes (grandchildren)
    # etc.
    
    # For this specific format:
    # - depth 0 = children of root (direct children)
    # - depth 1 = children of depth 0 nodes
    # - etc.
    
    # We need to track which node is the parent for each depth
    # Use a dict: depth -> node_name
    
    # Actually, let's use a simpler approach:
    # Track the current path as a list of node names
    # Each new line at depth D belongs to the parent at path[D-1]
    
    current_path = [root_name]  # Start with root
    path_nodes = [root]  # path_nodes[D] = node at depth D
    
    for line in lines[1:]:
        depth = count_indent(line)
        node_name = get_node_name(line)
        
        if depth == -1 or not node_name:
            continue
        
        # depth 0 = children of root
        # depth 1 = children of depth 0 nodes
        # etc.
        
        # For this input, depth is always 0 or positive
        # depth 0 means direct child of root
        
        if depth == 0:
            # Direct child of root
            child = {
                'name': node_name,
                'type': 'directory',
                'children': []
            }
            root['children'].append(child)
            # Current path resets to just root (we're now at children level)
            current_path = [root_name]
            path_nodes = [root]
        else:
            # depth > 0 means this is a grandchild or deeper
            # We need to find the parent at path[depth-1]
            
            # If we have enough nodes in path_nodes
            if depth - 1 < len(path_nodes):
                parent = path_nodes[depth - 1]
                
                # Check if parent has children
                if not parent.get('children'):
                    parent['children'] = []
                
                # Add as new child
                node = {
                    'name': node_name,
                    'type': 'directory',
                    'children': []
                }
                parent['children'].append(node)
                
                # Update path
                current_path = current_path[:depth + 1]
                current_path.append(node_name)
                path_nodes = path_nodes[:depth + 1]
                path_nodes.append(node)
            else:
                # This shouldn't happen with valid input
                pass
    
    return root


def merge_trees(trees: List[Dict[str, Any]]) -> Dict[int, Any]:
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
            add_node(existing_child, new_node)
        else:
            # If not, add the new node (using a copy to avoid mutating input)
            new_child_copy = copy.deepcopy(new_node)
            parent_node.setdefault('children', []).append(new_child_copy)

    for tree in trees:
        # We merge the top-level children of each tree into our global root
        for top_level_child in tree.get('children', []):
            add_node(root, top_level_child)
            
    # Sort by name for consistent ordering
    root['children'].sort(key=lambda x: x['name'])
    
    return root


def generate_ascii_tree(node: Dict[str, Any]) -> str:
    """
    Generate ASCII tree representation.
    
    Args:
        node: Node dictionary
    
    Returns:
        ASCII tree string
    """
    lines = []
    children = node.get('children', [])
    
    if not children:
        return ""
    
    # Process each child
    for i, child in enumerate(children):
        if i < len(children) - 1:
            # Not last - use │ for continuation
            indent = '│   '
        else:
            # Last - no continuation
            indent = '    '
        
        child_lines = generate_ascii_tree(child)
        if child_lines:
            lines.append(f"{indent}└───{child['name']}")
            lines.extend(child_lines)
        else:
            lines.append(f"{indent}└───{child['name']}")
    
    return '\n'.join(lines)


def split_into_trees(input_text: str) -> List[List[str]]:
    """
    Split input text into individual tree blocks.
    
    Args:
        input_text: Input text with multiple tree structures
    
    Returns:
        List of tree blocks
    """
    lines = input_text.strip().split('\n')
    
    trees = []
    current_block = []
    
    for line in lines:
        line = line
        if not line:
            continue
        
        # Check if this is a root line (starts with /nix/store)
        if line.startswith('/nix/store'):
            # Save previous block if exists
            if current_block:
                trees.append(current_block)
                current_block = []
            current_block = [line]
        else:
            # Continuation line (tree symbol)
            current_block.append(line)
    
    if current_block:
        trees.append(current_block)
    
    return trees


def process_tree_output(input_text: str) -> Dict[str, Any]:
    """
    Process input text and return merged tree as JSON.
    
    Args:
        input_text: Input text with multiple tree structures
    
    Returns:
        Dictionary with tree, json, and ascii keys
    """
    # Split into individual trees
    tree_blocks = split_into_trees(input_text)
    
    # Parse each tree
    tree_dicts = []
    for tree_lines in tree_blocks:
        if tree_lines:
            tree = parse_tree_block(tree_lines)
            tree_dicts.append(tree)
    
    # Merge all trees
    merged_tree = merge_trees(tree_dicts)
    
    # Generate JSON and ASCII representations
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
    
    Args:
        input_text: Input text containing multiple tree structures
    
    Returns:
        Dictionary containing JSON representation and ASCII tree
    """
    return process_tree_output(input_text)


def main():
    """Main function to demonstrate the merge functionality."""
    input_text = """/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/dygnwmswkg1v839pnd3zg6b4431ggbg0-system-path.drv
    └───/nix/store/vy9hrd513j41b4vc4708vkmsv0q7ic3c-xdg-utils-1.2.1.drv
        └───/nix/store/np97p7m6vpav7r1v824pjck5v2p0xzci-resholve-0.10.7.drv
/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/mi5kw37r0ndvd9w7fr9s1y5f063xhv0v-etc.drv
    └───/nix/store/0ibyb85glxh980wmnr1i1i1hm0xclh7l-system-units.drv
/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/dygnwmswkg1v839pnd3zg6b4431ggbg0-system-path.drv
    └───/nix/store/ydqg7di6cd4gvdfjv1c5hpmsjd2x7hdx-brave-1.88.138.drv
        └───/nix/store/hcydnrs0kr1sdj9mqz772vlp8qhp4cls-snappy-1.2.2.drv"""

    result = merge_nix_trees(input_text)
    
    print("JSON representation:")
    print(result['json'])
    print("\n\nASCII tree:")
    print(result['ascii'])
    
    return result


if __name__ == "__main__":
    main()
