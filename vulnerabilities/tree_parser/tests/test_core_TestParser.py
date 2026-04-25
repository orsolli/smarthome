import unittest
import os
from typing import Dict, Any

class TestParser(unittest.TestCase):
    @unittest.skipIf(not os.path.exists("tree_parser/core/parser.py"), "Parser implementation not yet present")
    def test_parser_split_logic(self):
        from tree_parser.core.parser import TreeParserImpl
        parser = TreeParserImpl()
        input_text = "/nix/store/a\n└───/nix/store/b\n/nix/store/c"
        trees = parser.split_into_trees(input_text)
        self.assertEqual(len(trees), 2)
        self.assertEqual(trees[0][0], "/nix/store/a")

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    unittest.main()
