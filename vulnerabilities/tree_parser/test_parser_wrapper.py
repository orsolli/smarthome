import unittest
from tree_parser.parser import parse_tree_block

class TestParser(unittest.TestCase):
    def test_parse_tree_block(self):
        input_text = """/nix/store/root
│   /nix/append/child-a
    │   /nix/append/grandchild-a1
    │   /nix/append/grandchild-a2
"""
        lines = input_text.strip().split('\n')
        result = parse_tree_block(lines)
        
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

if __name__ == "__main__":
    unittest.main()
