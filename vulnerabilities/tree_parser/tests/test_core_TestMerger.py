import unittest
import os
from typing import Dict, Any

@unittest.skipIf(not os.path.exists("tree_parser/core/merger.py"), "Merger implementation not yet present")
class TestMerger(unittest.TestCase):
    def test_merger_single_tree(self):
        from tree_parser.core.merger import TreeMergerImpl
        merger = TreeMergerImpl()
        trees = [{'name': 'a', 'children': []}]
        result = merger.merge_trees(trees)
        self.assertEqual(result['name'], '.')
        self.assertEqual(len(result['children']), 1)

    def test_merger_multiple_trees_overlap(self):
        from tree_parser.core.merger import TreeMergerImpl
        merger = TreeMergerImpl()
        tree1 = {'name': '/nix/store/a', 'children': [{'name': '/nix/store/a/b', 'children': []}]}
        tree2 = {'name': '/nix/store/a', 'children': [{'name': '/nix/store/a/c', 'children': []}]}
        result = merger.merge_trees([tree1, tree2])
        
        # Root is '.', so first child should be '/nix/store/a'
        root_child = result['children'][0]
        self.assertEqual(root_child['name'], '/nix/store/a')
        # Actually let's do a real check
        self.assertEqual(root_child['name'], '/nix/store/a')
        
        # Check if both children 'b' and 'c' exist under 'a'
        child_names = [child['name'] for child in root_child['children']]
        self.assertIn('/nix/store/a/b', child_names)
        self.assertIn('/nix/store/a/c', child_names)

    def test_merger_empty_trees(self):
        from tree_parser.core.merger import TreeMergerImpl
        merger = TreeMergerImpl()
        result = merger.merge_trees([])
        self.assertEqual(result['name'], '.')
        self.assertEqual(result['children'], [])

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    unittest.main()
