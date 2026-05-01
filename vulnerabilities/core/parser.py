from typing import List, Dict, Any
from interfaces.TreeParser import TreeParserInterface

def _count_indent(line: str) -> int:
    """
    Count the indentation level of a tree line.
    
    Each level is represented by 4 characters:
    - │   (vertical bar + 3 spaces)
    -     (4 spaces)
    
    Returns the number of indentation groups.
    """
    if not line.strip():
        return -1
    
    count = 0
    i = 0
    while i + 4 <= len(line):
        chunk = line[i:i+4]
        if chunk == '│   ' or chunk == '└───' or chunk == '├───' or chunk == '    ':
            count += 1
            i += 4
        else:
            break
    
    return count


def _get_node_name(line: str) -> str:
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

class TreeParserImpl(TreeParserInterface):
    def parse_tree_block(self, lines: List[str]) -> Dict[str, Any]:
        lines = [line_ for line_ in lines if line_.strip()]
        
        if not lines:
            return {'name': '.', 'type': 'directory', 'children': []}
        
        root_name = lines[0].strip()
        root = {'name': root_name, 'str_name': root_name, 'type': 'directory', 'children': []}
        
        path_nodes = [root]
        
        for line in lines[1:]:
            depth = _count_indent(line)
            node_name = _get_node_name(line)
            
            if depth == -1 or not node_name:
                continue
            
            if depth == 0:
                child = {
                    'name': node_name,
                    'type': 'directory',
                    'children': []
                }
                root['children'].append(child)
                path_nodes = [root, child]
            else:
                if depth - 1 < len(path_nodes):
                    parent = path_nodes[depth - 1]
                    if 'children' not in parent:
                        parent['children'] = []
                    
                    node = {
                        'name': node_name,
                        'name_str': node_name,
                        'type': 'directory',
                        'children': []
                    }
                    parent['children'].append(node)
                    
                    path_nodes = path_nodes[:depth + 1]
                    path_nodes.append(node)
                else:
                    pass
        return root

    def split_into_trees(self, input_text: str) -> List[List[str]]:
        lines = input_text.strip().split('\n')
        trees = []
        current_block = []
        
        for line in lines:
            if not line.strip():
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
