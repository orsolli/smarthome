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
        input_text = "/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-a-b-c.drv\n└───/nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-d-e-f.1.drv\n/nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-g-h-i.j.k.drv"
        trees = parser.split_into_trees(input_text)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0][0], "/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-a-b-c.drv")

    def test_parse_tree_block(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = """/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-root-1.0.drv
│   /nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-child-a-1.0.drv
    │   /nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild1-a1-1.0.drv
    │   /nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild2-a2-1.0.drv
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], 'root')
        
        # Check child
        self.assertEqual(len(result['children']), 1)
        self.assertEqual(result['children'][0]['name'], 'child-a')
        
        # Check grandchild
        self.assertEqual(len(result['children'][0]['children']), 2)
        grandchild_names = [gc['name'] for gc in result['children'][0]['children']]
        self.assertIn('grandchild1-a1', grandchild_names)
        self.assertIn('grandchild2-a2', grandchild_names)

    def test_complex_tree(self):
        from core.parser import TreeParserImpl
        parser = TreeParserImpl()
        # A more complex tree structure
        input_text = """/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-root-1.0.drv
│   /nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-child-a-1.0.drv
│   │   /nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild-a1-1.0.drv
│   │   /nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild-a2-1.0.drv
│   /nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-child-b-1.0.drv
    /nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-sibling-1.0.drv
"""
        lines = input_text.strip().split('\n')
        result = parser.parse_tree_block(lines)
        
        # Check root
        self.assertEqual(result['name'], 'root')

if __name__ == "__main__":
    unittest.main()
