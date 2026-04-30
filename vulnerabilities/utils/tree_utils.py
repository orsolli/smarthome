def count_indent(line: str) -> int:
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
