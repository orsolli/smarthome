from typing import Dict, Any
from ..interfaces.TreeFormatter import TreeFormatterInterface

class TreeFormatterImpl(TreeFormatterInterface):
    def generate_ascii_tree(self, node: Dict[str, Any]) -> str:
        lines = []
        children = node.get('children', [])
        
        if not children:
            return ""
        
        for i, child in enumerate(children):
            if i < len(children) - 1:
                indent = '│   '
            else:
                indent = '    '
            
            child_lines = self.generate_ascii_tree(child)
            if child_lines:
                lines.append(f"{indent}└───{child['name']}")
                lines.extend(child_lines.split('\n'))
            else:
                lines.append(f"{indent}└───{child['name']}")
        
        return '\n'.join(lines)
