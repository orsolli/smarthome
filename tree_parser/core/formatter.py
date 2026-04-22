from typing import Dict, Any
from ..interfaces.TreeFormatter import TreeFormatterInterface


class TreeFormatterImpl(TreeFormatterInterface):
    def generate_ascii_tree(self, node: Dict[str, Any]) -> str:
        """Generate ASCII tree representation."""
        children = node.get('children', [])
        
        # Skip synthetic '.' root node from merger
        if node.get('name') == '.' and len(children) > 0:
            lines = self._format_children_top_level(node, children)
            return '\n'.join(lines) + '\n'
        
        lines = [node.get('name', '')]
        
        if not children:
            return lines[0]
        
        for i, child in enumerate(children):
            if i == len(children) - 1:
                connector = '└───'
                next_prefix = "    "
            else:
                connector = '├───'
                next_prefix = "|   "
            
            lines.append(connector + child.get('name', ''))
            
            child_lines = self._format_children(
                child, 
                child.get('children', []),
                next_prefix
            )
            if child_lines:
                lines.extend(child_lines.split('\n'))
        
        return '\n'.join(lines) + '\n'
    
    def _format_children_top_level(self, node: Dict[str, Any], children: list) -> list:
        """Format children of the synthetic '.' root as top-level (no connector prefix)."""
        lines = []
        for i, child in enumerate(children):
            if i == len(children) - 1:
                connector = '└───'
                next_prefix = "    "
            else:
                connector = '├───'
                next_prefix = "|   "
            
            lines.append(connector + child.get('name', ''))
            
            grand_children = child.get('children', [])
            if grand_children:
                grand_children_lines = self._format_children(
                    child, grand_children, next_prefix
                )
                if grand_children_lines:
                    lines.extend(grand_children_lines.split('\n'))
        
        return lines
    
    def _format_children(self, node: Dict[str, Any], children: list, prefix: str) -> str:
        """Format children of a node recursively."""
        lines = []
        for i, child in enumerate(children):
            if i == len(children) - 1:
                connector = '└───'
                next_prefix = prefix + "    "
            else:
                connector = '├───'
                next_prefix = prefix + "|   "
            
            lines.append(prefix + connector + child.get('name', ''))
            
            grand_children = child.get('children', [])
            if grand_children:
                grand_children_lines = self._format_children(
                    child, grand_children, next_prefix
                )
                if grand_children_lines:
                    lines.extend(grand_children_lines.split('\n'))
        
        return '\n'.join(lines)
