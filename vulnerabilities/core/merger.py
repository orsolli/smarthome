"""Merger module for consolidating dependency trees.

Uses the local tree_parser to merge multiple why-depends output trees
into a single consolidated tree structure.

The merger converts between the original dependency tree format
(with pname and drv_path keys) and tree_parser's display-oriented format
(with name and str_name keys).
"""

import copy
from typing import Any, Sequence, List

from interfaces import TreeMergerInterface, TreeNodeDict


def _trees_to_text(trees: Sequence[TreeNodeDict]) -> str:
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


def _dict_to_text(node: TreeNodeDict, indent: int = 0) -> str:
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


class TreeMergerImpl(TreeMergerInterface):
    """Implementation of TreeMergerInterface using tree_parser."""

    def merge_trees(self, trees: list[TreeNodeDict]) -> TreeNodeDict | None:
        """Merge multiple dependency trees into one.

        Args:
            dependency_trees: List of tree dicts from DependencyMapper.

        Returns:
            A consolidated tree dict with overlapping paths merged.
        """
        if not trees:
            return None
        
        root: TreeNodeDict = {'name': '.', 'pname': '', 'drv_path': '', 'children': []}
        
        def add_node(parent_node: TreeNodeDict, new_node: TreeNodeDict):
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

        children = root['children']
        if len(children) <= 1:
            return children[0]

        children.sort(key=lambda x: x['name'])
        return root