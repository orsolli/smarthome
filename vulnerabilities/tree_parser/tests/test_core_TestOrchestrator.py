import unittest
import os
from typing import Dict, Any


class TestOrchestrator(unittest.TestCase):
    @unittest.skipIf(not os.path.exists("tree_parser/core/orchestrator.py"), "Orchestrator implementation not yet present")
    def test_orchestrator(self):
        from tree_parser.core.parser import TreeParserImpl
        from tree_parser.core.merger import TreeMergerImpl
        from tree_parser.core.formatter import TreeFormatterImpl
        from tree_parser.core.orchestrator import TreeOrchestrator
        parser = TreeParserImpl()
        merger = TreeMergerImpl()
        formatter = TreeFormatterImpl()
        orchestrator = TreeOrchestrator(parser, merger, formatter)
        input_text = """/root/path/a.txt
└───/first-child
    └───first-grand-child
        └───/deep-child
/root/path/a.txt
└───second/child
    └───/bastard
/root/path/a.txt
└───/first-child
    └───/second/grand-child
        └───snappy
"""
        output_text = """└───/root/path/a.txt
    ├───/first-child
    |   ├───first-grand-child
    |   |   └───/deep-child
    |   └───/second/grand-child
    |       └───snappy
    └───second/child
        └───/bastard
"""
        result = orchestrator.merge_nix_trees(input_text)
        self.assertEqual(result["ascii"], output_text)

    def test_recursive_merge(self):
        """Test that nested children are correctly merged."""
        from tree_parser.core.parser import TreeParserImpl
        from tree_parser.core.merger import TreeMergerImpl
        from tree_parser.core.formatter import TreeFormatterImpl
        from tree_parser.core.orchestrator import TreeOrchestrator
        parser = TreeParserImpl()
        merger = TreeMergerImpl()
        formatter = TreeFormatterImpl()
        orchestrator = TreeOrchestrator(parser, merger, formatter)
        input_text = """/nix/store/root
└───/nix/store/child-a
    └───/nix/store/grandchild-a1
/nix/store/root
└───/nix/store/child-a
    └───/nix/store/grandchild-a2
"""
        result = orchestrator.merge_nix_trees(input_text)
        
        # Find child-a in the results
        child_a = None
        for root in result['tree']['children']:
            if root['name'] == '/nix/store/root':
                child = root['children'][0]
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
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    unittest.main()
