"""Merger module for consolidating dependency trees.

Uses the local tree_parser to merge multiple why-depends output trees
into a single consolidated tree structure.
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
        A consolidated tree dict with overlapping paths merged.
    """
    if not dependency_trees:
        return {}

    # Serialize trees to text format for tree_parser
    text_input = _trees_to_text(dependency_trees)

    # Use tree_parser to merge
    merged = merge_nix_trees(text_input)

    return merged


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
