from typing import Dict, Any

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
            lines.extend(child_lines.split('\n'))
        else:
            lines.append(f"{indent}└───{child['name']}")
    
    return '\n'.join(lines)
