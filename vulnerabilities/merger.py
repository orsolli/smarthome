"""Merger module for consolidating dependency trees.

Uses the local tree_parser to merge multiple why-depends output trees
into a single consolidated tree structure.

The merger converts between the original dependency tree format
(with pname and drv_path keys) and tree_parser's display-oriented format
(with name and str_name keys).
"""

from typing import Any

from tree_parser import merge_nix_trees


def merge_dependency_trees(
    dependency_trees: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge multiple dependency trees into a single consolidated tree.

    Args:
        dependency_trees: List of dependency tree dicts from why-depends.

    Returns:
        A consolidated tree dict with overlapping paths merged,
        in the original format (pname, drv_path, children keys).
    """
    if not dependency_trees:
        return {}

    # Serialize trees to text format for tree_parser
    text_input = _trees_to_text(dependency_trees)

    # Use tree_parser to merge
    merged_raw = merge_nix_trees(text_input)

    # Extract the actual tree and convert back to original format
    tree_data = merged_raw.get("tree", merged_raw)
    return _tree_to_dict(tree_data)


def _trees_to_text(trees: list[dict[str, Any]]) -> str:
    """Convert a list of dependency tree dicts to text format.

    Args:
        trees: List of tree dicts.

    Returns:
        Text representation suitable for tree_parser.
    """
    parts: list[str] = []
    for tree in trees:
        if tree:
            parts.append(_dict_to_text(tree))
    return "\n".join(parts)


def _dict_to_text(node: dict[str, Any], indent: int = 0) -> str:
    """Recursively convert a tree dict to text representation.

    Args:
        node: A tree node dict with drv_path and children keys.
        indent: Current indentation level.

    Returns:
        Text representation of the tree.
    """
    prefix = "\u2514\u2500\u2500" + "\u2500" * indent
    drv_path = node.get("drv_path", "")
    pname = node.get("pname", "")
    display = f"{pname} ({drv_path})" if pname else drv_path
    lines = [f"{prefix}{display}"]
    for child in node.get("children", []):
        lines.append(_dict_to_text(child, indent + 1))
    return "\n".join(lines)


def _tree_to_dict(tree_node: dict[str, Any]) -> dict[str, Any]:
    """Convert a tree_parser tree node back to the original format.

    tree_parser outputs nodes with name, str_name, type, children keys.
    This converts them back to pname, drv_path, children keys.

    Args:
        tree_node: A tree_parser tree node dict.

    Returns:
        A dict in the original format.
    """
    name = tree_node.get("name", "")
    str_name = tree_node.get("str_name", "")

    # Extract pname and drv_path from the display name.
    # Format: "└──pname (/nix/store/...-drv.drv)" or "pname (/nix/store/...-drv.drv)"
    # Strip tree drawing characters and extract pname and drv_path.
    pname, drv_path = _parse_display_name(name)

    return {
        "pname": pname,
        "drv_path": drv_path,
        "children": [_tree_to_dict(child) for child in tree_node.get("children", [])],
    }


def _parse_display_name(name: str) -> tuple[str, str]:
    """Parse a tree_parser display name into pname and drv_path.

    Args:
        name: Display name from tree_parser (e.g., "└──nixos-system-OrjanAMD (/nix/store/...-system.drv)")

    Returns:
        Tuple of (pname, drv_path).
    """
    # Find the opening parenthesis to separate pname from drv_path
    paren_idx = name.find(" (")
    if paren_idx == -1:
        # No paren found; treat entire name as pname, empty drv_path
        # Strip tree drawing characters
        clean = _strip_tree_chars(name)
        return clean, ""

    pname_part = name[:paren_idx]
    drv_path_part = name[paren_idx + 2:-1]  # Strip " (" prefix and ")" suffix

    # Strip tree drawing characters from pname
    pname = _strip_tree_chars(pname_part)

    return pname, drv_path_part


def _strip_tree_chars(s: str) -> str:
    """Strip tree drawing characters from a string.

    Args:
        s: String with tree drawing characters.

    Returns:
        String with tree drawing characters removed.
    """
    # Remove common tree drawing characters: └──, ├──, └, ─, │, etc.
    import re
    return re.sub(r'^[\u2514\u251c\u2502\u2500]+', '', s)
