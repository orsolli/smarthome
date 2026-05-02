from typing import List
from interfaces.TreeParser import TreeParserInterface
from interfaces.TreeNodeDict import TreeNodeDict


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


def _extract_name_from_path(path: str) -> tuple[str, str]:
    """Extract name-version and package name from a derivation path.
    
    For '/nix/store/xyz-root-1.0.drv' returns ('root-1.0', 'root').
    For '/nix/store/child-a-1.0.drv' returns ('a-1.0', 'a').
    For non-nix paths returns (path, '').
    """
    # Get the filename component
    if '/nix/store/' in path:
        filename = path.rsplit('/nix/store/', 1)[-1]
    else:
        filename = path
    
    # Strip .drv extension
    name = filename
    if name.endswith('.drv'):
        name = name[:-4]
    
    # Take last two -separated components and join with -
    parts = name.rsplit('-', 2)
    if len(parts) >= 2:
        name = '-'.join(parts[-2:])
    
    return name, '-'.join(parts[1:-1])


def _get_node_name(line: str) -> tuple[str, str, str]:
    """Get the node names and drv_path from a tree line.
    
    Returns a tuple of (name, pname, drv_path).
    """
    line = line.strip()
    if not line:
        return "", "", ""
    
    # Find where the path starts (after tree symbols and spaces)
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
    
    raw_path = line[i:].strip()
    # Only extract name from nix store paths; preserve other paths as-is
    if '/nix/store/' in raw_path:
        return *_extract_name_from_path(raw_path), raw_path
    return raw_path, "", raw_path


class TreeParserImpl(TreeParserInterface):
    def parse_tree_block(self, lines: List[str]) -> TreeNodeDict:
        lines = [line_ for line_ in lines if line_.strip()]
        
        if not lines:
            return
        
        # Extract just the name from the root path (e.g., "root-1.0" from "/nix/store/xyz-root-1.0.drv")
        root_path = lines[0].strip()
        root_name, root_pname = _extract_name_from_path(root_path)
        
        root: TreeNodeDict = {
            'name': root_name,
            'pname': root_pname,
            'drv_path': root_path,
            'children': []
        }
        
        path_nodes: list[TreeNodeDict] = [root]
        
        for line in lines[1:]:
            depth = _count_indent(line)
            name, pname, drv_path = _get_node_name(line)
            
            if depth == -1 or not name:
                continue
            
            if depth == 0:
                child: TreeNodeDict = {
                    'name': name,
                    'pname': pname,
                    'drv_path': drv_path,
                    'children': []
                }
                root['children'].append(child)
                path_nodes.append(child)
            else:
                if depth - 1 < len(path_nodes):
                    parent = path_nodes[depth - 1]
                    if 'children' not in parent:
                        parent['children'] = []
                    
                    node: TreeNodeDict = {
                        'name': name,
                        'pname': pname,
                        'drv_path': drv_path,
                        'children': []
                    }
                    parent['children'].append(node)
                    
                    # Trim path_nodes to current depth + new node
                    path_nodes = path_nodes[:depth]
                    path_nodes.append(node)
                else:
                    pass
        
        return root

    def split_into_trees(self, input_text: str) -> List[List[str]]:
        lines = input_text.strip().split('\n')
        trees: List[List[str]] = []
        current_block: List[str] = []
        
        for line in lines:
            if not line.strip():
                continue
            
            if line.startswith('/') and line != '/nix/store':
                if current_block:
                    trees.append(current_block)
                    current_block = []
                current_block = [line]
            else:
                current_block.append(line)
        
        if current_block:
            trees.append(current_block)
        
        return trees
