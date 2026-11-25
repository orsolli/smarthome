import unittest
import os
from typing import Dict, Any

@unittest.skipIf(not os.path.exists("core/formatter.py"), "Formatter implementation not yet present")
class TestFormatter(unittest.TestCase):
    def test_formatter_simple_tree(self):
        from core.formatter import TreeFormatterImpl
        formatter = TreeFormatterImpl()
        tree = {'name': 'root', 'children': [{'name': 'child', 'children': []}]}
        output = formatter.generate_ascii_tree(tree)
        self.assertIn('└───child', output)

    def test_formatter_deep_tree(self):
        from core.formatter import TreeFormatterImpl
        formatter = TreeFormatterImpl()
        tree = {
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

        output = formatter.generate_ascii_tree(tree)
        self.assertEqual(output, """/root/path/a.txt
├───/first-child
|   ├───first-grand-child
|   |   └───/deep-child
|   └───/second/grand-child
|       └───snappy
└───second/child
    └───/bastard
""")

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
