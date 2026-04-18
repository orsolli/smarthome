import unittest
from tree_parser.parser import merge_nix_trees

class TestMergeTrees(unittest.TestCase):
    def test_recursive_merge(self):
        """Test that nested children are correctly merged."""
        input_text = """/nix/store/root
└───/nix/store/child-a
    └───/nix/store/grandchild-a1
/nix/store/root
└───/nix/store/child-a
    └───/nix/store/grandchild-a2
"""
        result = merge_nix_trees(input_text)
        
        # Find child-a in the results
        child_a = None
        for child in result['tree']['children']:
            if child['name'] == '/nix/store/child-a':
                child_a = child
                break
        
        self.assertIsNotNone(child_a, "child-a should exist in the merged tree")
        
        # Check if both grandchildren exist
        grandchild_names = [gc['name'] for gc in child_a['children']]
        self.assertIn('/nix/store/grandchild-a1', grandchild_names)
        self.assertIn('/nix/store/grandchild-a2', grandchild_names)
        self.assertEqual(len(grandchild_names), 2)

if __name__ == "__main__":
    unittest.main()
