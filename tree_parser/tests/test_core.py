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

class TestMerger(unittest.TestCase):
    @unittest.skipIf(not os.path.exists("tree_parser/core/merger.py"), "Merger implementation not yet present")
    def test_merger_single_tree(self):
        from tree_parser.core.merger import TreeMergerImpl
        merger = TreeMergerImpl()
        trees = [{'name': 'a', 'children': []}]
        result = merger.merge_trees(trees)
        self.assertEqual(result['name'], '.')
        self.assertEqual(len(result['children']), 1)

    @unittest.skipIf(not os.path.exists("tree_parser/core/merger.py"), "Merger implementation not yet present")
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

    @unittest.skipIf(not os.path.exists("tree_parser/core/merger.py"), "Merger implementation not yet present")
    def test_merger_empty_trees(self):
        from tree_parser.core.merger import TreeMergerImpl
        merger = TreeMergerImpl()
        result = merger.merge_trees([])
        self.assertEqual(result['name'], '.')
        self.assertEqual(result['children'], [])

class TestFormatter(unittest.TestCase):
    @unittest.skipIf(not os.path.exists("tree_parser/core/formatter.py"), "Formatter implementation not yet present")
    def test_formatter_simple_tree(self):
        from tree_parser.core.formatter import TreeFormatterImpl
        formatter = TreeFormatterImpl()
        tree = {'name': 'root', 'children': [{'name': 'child', 'children': []}]}
        output = formatter.generate_ascii_tree(tree)
        self.assertIn('└───child', output)

    @unittest.skipIf(not os.path.exists("tree_parser/core/formatter.py"), "Formatter implementation not yet present")
    def test_formatter_deep_tree(self):
        from tree_parser.core.formatter import TreeFormatterImpl
        formatter = TreeFormatterImpl()
        tree = {
          "name": ".",
          "type": "directory",
          "children": [
            {
              "name": "/root/path/a.txt",
              "str_name": "/root/path/a.txt",
              "type": "directory",
              "children": [
                {
                  "name": "/first-child",
                  "name_str": "/first-child",
                  "type": "directory",
                  "children": [
                    {
                      "name": "first-grand-child",
                      "name_str": "first-grand-child",
                      "type": "directory",
                      "children": [
                        {
                          "name": "/deep-child",
                          "name_str": "/deep-child",
                          "type": "directory",
                          "children": []
                        }
                      ]
                    },
                    {
                      "name": "/second/grand-child",
                      "name_str": "/second/grand-child",
                      "type": "directory",
                      "children": [
                        {
                          "name": "snappy",
                          "name_str": "snappy",
                          "type": "directory",
                          "children": []
                        }
                      ]
                    }
                  ]
                },
                {
                  "name": "second/child",
                  "name_str": "second/child",
                  "type": "directory",
                  "children": [
                    {
                      "name": "/bastard",
                      "name_str": "/bastard",
                      "type": "directory",
                      "children": []
                    }
                  ]
                }
              ]
            }
          ]
        }

        output = formatter.generate_ascii_tree(tree)
        self.assertIn("""/root/path/a.txt
├───/first-child
|   ├───first-grand-child
|   |   └───/deep-child
|   └───/second/grand-child
|       └───snappy
└───second/child
    └───/bastard
""", output)

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
    unittest.main()
