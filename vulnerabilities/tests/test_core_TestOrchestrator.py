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
        input_text = """/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-root.drv
└───/nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-child-a.drv
    └───/nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild-a1.drv
/nix/store/a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6-root.drv
└───/nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-child-a.drv
    └───/nix/store/g1h2i3j4k5l6m7n8o9p0q1r2s3t4u5v6-grandchild-a2.drv
/nix/store/b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6-rootb.drv
└───/nix/store/c1d2e3f4g5h6i7j8k9l0m1n2o3p4q5r6-childb-ab.drv
    └───/nix/store/d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6-grandchildb-a2b.drv
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
