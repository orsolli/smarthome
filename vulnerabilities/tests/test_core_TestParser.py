import unittest
import os
from typing import Dict, Any

@unittest.skipIf(not os.path.exists("core/parser.py"), "Parser implementation not yet present")
class TestParser(unittest.TestCase):
    def test_parser_split_logic(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = "/nix/store/a\n└───/nix/store/b\n/nix/store/c"
        trees = parser.split_into_trees(input_text)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0][0], "/nix/store/a")

    def test_parse_tree_block(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = """/nix/store/root
│   /nix/append/child-a
    │   /nix/append/grandchild-a1
    │   /nix/append/grandchild-a2
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], '/nix/store/root')
        
        # Check child
        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['children'][0]['name'], '/nix/append/child-a')
        
        # Check grandchild
        self.assertEqual(len(result['children'][0]['children']), 2)
        grandchild_names = [gc['name'] for gc in result['children'][0]['children']]
        self.assertIn('/nix/append/grandchild-a1', grandchild_names)
        self.assertIn('/nix/append/grandchild-a2', grandchild_names)

    def test_complex_tree(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        # A more complex tree structure
        input_text = """/nix/store/root
│   /nix/append/child-a
│   │   /nix/append/grandchild-a1
│   │   /nix/append/grandchild-a2
│   /nix/append/child-b
    /nix/other/sibling
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], '/nix/store/root')

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
