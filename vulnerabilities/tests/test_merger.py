"""Tests for merger module."""

import os
import tempfile
import unittest

from core.merger import merge_dependency_trees, _dict_to_text, _trees_to_text


class TestDictToText(unittest.TestCase):
    def test_simple_node(self):
        """A single node with no children produces one line."""
        node = {"drv_path": "/nix/store/abc.drv", "pname": "test-pkg"}
        result = _dict_to_text(node)
        self.assertIn("test-pkg", result)
        self.assertIn("/nix/store/abc.drv", result)

    def test_node_with_children(self):
        """A node with children produces indented child lines."""
        node = {
            "drv_path": "/nix/store/parent.drv",
            "pname": "parent",
            "children": [
                {"drv_path": "/nix/store/child.drv", "pname": "child"}
            ],
        }
        result = _dict_to_text(node)
        lines = result.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertIn("parent", lines[0])
        self.assertIn("child", lines[1])


class TestTreesToText(unittest.TestCase):
    def test_empty_list(self):
        """An empty list returns empty string."""
        result = _trees_to_text([])
        self.assertEqual(result, "")

    def test_single_tree(self):
        """A single tree is converted to text."""
        trees = [{"drv_path": "/nix/store/a.drv", "pname": "a"}]
        result = _trees_to_text(trees)
        self.assertIn("a", result)

    def test_multiple_trees(self):
        """Multiple trees are separated by newlines."""
        trees = [
            {"drv_path": "/nix/store/a.drv", "pname": "a"},
            {"drv_path": "/nix/store/b.drv", "pname": "b"},
        ]
        result = _trees_to_text(trees)
        self.assertIn("a", result)
        self.assertIn("b", result)


class TestMergeDependencyTrees(unittest.TestCase):
    def test_empty_input(self):
        """Empty input returns empty dict."""
        result = merge_dependency_trees([])
        self.assertEqual(result, {})

    def test_single_tree(self):
        """A single tree is returned (possibly modified by tree_parser)."""
        trees = [
            {
                "drv_path": "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
                "pname": "nixos-system-OrjanAMD",
                "children": [
                    {
                        "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
                        "pname": "Diff",
                        "children": [],
                    }
                ],
            }
        ]
        result = merge_dependency_trees(trees)
        self.assertIsInstance(result, dict)

    def test_multiple_trees(self):
        """Multiple trees are merged."""
        trees = [
            {
                "drv_path": "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
                "pname": "nixos-system-OrjanAMD",
                "children": [
                    {
                        "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
                        "pname": "Diff",
                        "children": [],
                    }
                ],
            },
            {
                "drv_path": "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
                "pname": "nixos-system-OrjanAMD",
                "children": [
                    {
                        "drv_path": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
                        "pname": "ShellCheck",
                        "children": [],
                    }
                ],
            },
        ]
        result = merge_dependency_trees(trees)
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
