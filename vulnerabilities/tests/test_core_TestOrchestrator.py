import unittest
import os
from typing import Dict, Any


@unittest.skipIf(not os.path.exists("core/orchestrator.py"), "Orchestrator implementation not yet present")
class TestOrchestrator(unittest.TestCase):
    def test_orchestrator(self):
        from core.parser import TreeParserImpl
        from core.merger import TreeMergerImpl
        from core.formatter import TreeFormatterImpl
        from core.orchestrator import TreeOrchestrator
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
        output_text = """/root/path/a.txt
├───/first-child
|   ├───first-grand-child
|   |   └───/deep-child
|   └───/second/grand-child
|       └───snappy
└───second/child
    └───/bastard
"""
        result = orchestrator.process_tree_output(input_text)
        self.assertEqual(result["ascii"], output_text)

    def test_recursive_merge(self):
        """Test that nested children are correctly merged."""
        from core.parser import TreeParserImpl
        from core.merger import TreeMergerImpl
        from core.formatter import TreeFormatterImpl
        from core.orchestrator import TreeOrchestrator
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
/nix/store/rootb
└───/nix/store/childb-ab
    └───/nix/store/grandchildb-a2b
"""
        result = orchestrator.process_tree_output(input_text)
        
        # Find child-a in the results
        child_a = None
        for root in result['tree']['children']:
            if root['name'] == 'root':
                child = root['children'][0]
                if child['name'] == 'child-a':
                    child_a = child
                    break
        
        self.assertIsNotNone(child_a, "child-a should exist in the merged tree")
        
        # Check if both grandchildren exist
        grandchild_names = [gc['name'] for gc in child_a['children']]
        self.assertIn('grandchild-a1', grandchild_names)
        self.assertIn('grandchild-a2', grandchild_names)
        self.assertEqual(len(grandchild_names), 2)

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
