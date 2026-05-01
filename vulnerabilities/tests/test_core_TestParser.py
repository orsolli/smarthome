import unittest
import os
from typing import Dict, Any

import sys
sys.path.append(os.getcwd().split('/tests')[0])

@unittest.skipIf(not os.path.exists("core/parser.py"), "Parser implementation not yet present")
class TestParser(unittest.TestCase):
    def test_parser_split_logic(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = "/nix/store/a-b-c.drv\n└───/nix/store/d-e-f.1.drv\n/nix/store/g-h-i.j.k.drv"
        trees = parser.split_into_trees(input_text)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0][0], "/nix/store/a")

    def test_parse_tree_block(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = """/nix/store/xyz-root-1.0.drv
│   /nix/store/child-a-1.0.drv
    │   /nix/store/grandchild1-a1-1.0.drv
    │   /nix/store/grandchild2-a2-1.0.drv
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], 'root-1.0')
        
        # Check child
        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['children'][0]['name'], 'a-1.0')
        
        # Check grandchild
        self.assertEqual(len(result['children'][0]['children']), 2)
        grandchild_names = [gc['name'] for gc in result['children'][0]['children']]
        self.assertIn('a1-1.0', grandchild_names)
        self.assertIn('a2-1.0', grandchild_names)

    def test_complex_tree(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        # A more complex tree structure
        input_text = """/nix/store/root-1.0.drv
│   /nix/append/child-a-1.0.drv
│   │   /nix/append/grandchild-a1-1.0.drv
│   │   /nix/append/grandchild-a2-1.0.drv
│   /nix/append/child-b-1.0.drv
    /nix/other/sibling-1.0.drv
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], 'oot-1.0')

if __name__ == "__main__":
    unittest.main()
