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
        output_text = """/root/path/a.txt
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

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    unittest.main()
