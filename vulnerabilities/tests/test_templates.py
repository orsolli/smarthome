"""Tests for app/templates.py."""

import unittest

from app.templates import (
    base_html,
    tree_node_html,
    tree_html,
)


class TestBaseHtml(unittest.TestCase):
    """Tests for base_html template."""

    def test_contains_htmx(self):
        """Base HTML includes HTMX script."""
        html = base_html("Test", "Body")
        self.assertIn("htmx.org", html)

    def test_contains_title(self):
        """Base HTML includes the given title."""
        html = base_html("My Title", "Body")
        self.assertIn("My Title", html)

    def test_contains_body(self):
        """Base HTML includes the given body."""
        html = base_html("Title", "Custom body content")
        self.assertIn("Custom body content", html)

    def test_contains_severity_styles(self):
        """Base HTML includes severity CSS classes."""
        html = base_html("Title", "Body")
        self.assertIn("sev-CRITICAL", html)
        self.assertIn("sev-HIGH", html)
        self.assertIn("sev-MEDIUM", html)
        self.assertIn("sev-LOW", html)


class TestTreeNodeHtml(unittest.TestCase):
    """Tests for tree_node_html template."""

    def test_leaf_node_no_children(self):
        """Leaf node renders without expand arrow."""
        node = {"pname": "test-pkg", "drv_path": "/nix/store/abc-test-1.0.drv"}
        html = tree_node_html(node, {}, expanded=False)
        self.assertIn("leaf", html)
        self.assertNotIn("tree-children", html)

    def test_parent_node_has_children(self):
        """Parent node renders with expand arrow and children container."""
        node = {
            "pname": "parent-pkg",
            "drv_path": "/nix/store/abc-parent-1.0.drv",
            "children": [
                {"pname": "child-pkg", "drv_path": "/nix/store/def-child-1.0.drv"}
            ],
        }
        html = tree_node_html(node, {}, expanded=True)
        self.assertIn("expanded", html)
        self.assertIn("tree-children", html)

    def test_critical_severity(self):
        """Node with CVSS >= 9.0 gets CRITICAL severity."""
        node = {
            "pname": "vuln-pkg",
            "drv_path": "/nix/store/abc-vuln-1.0.drv",
            "children": [],
        }
        vuln_map = {
            "/nix/store/abc-vuln-1.0.drv": {
                "cvssv3_basescore": {"CVE-2024-001": 9.5}
            }
        }
        html = tree_node_html(node, vuln_map)
        self.assertIn("sev-CRITICAL", html)
        self.assertIn("CRITICAL", html)

    def test_high_severity(self):
        """Node with CVSS >= 7.0 gets HIGH severity."""
        node = {
            "pname": "high-pkg",
            "drv_path": "/nix/store/abc-high-1.0.drv",
            "children": [],
        }
        vuln_map = {
            "/nix/store/abc-high-1.0.drv": {
                "cvssv3_basescore": {"CVE-2024-002": 7.5}
            }
        }
        html = tree_node_html(node, vuln_map)
        self.assertIn("sev-HIGH", html)
        self.assertIn("HIGH", html)

    def test_medium_severity(self):
        """Node with CVSS >= 4.0 gets MEDIUM severity."""
        node = {
            "pname": "med-pkg",
            "drv_path": "/nix/store/abc-med-1.0.drv",
            "children": [],
        }
        vuln_map = {
            "/nix/store/abc-med-1.0.drv": {
                "cvssv3_basescore": {"CVE-2024-003": 5.0}
            }
        }
        html = tree_node_html(node, vuln_map)
        self.assertIn("sev-MEDIUM", html)
        self.assertIn("MEDIUM", html)

    def test_low_severity(self):
        """Node with CVSS < 4.0 gets LOW severity."""
        node = {
            "pname": "low-pkg",
            "drv_path": "/nix/store/abc-low-1.0.drv",
            "children": [],
        }
        vuln_map = {
            "/nix/store/abc-low-1.0.drv": {
                "cvssv3_basescore": {"CVE-2024-004": 2.0}
            }
        }
        html = tree_node_html(node, vuln_map)
        self.assertIn("sev-LOW", html)
        self.assertIn("LOW", html)

    def test_none_severity(self):
        """Node not in vuln_map gets NONE severity."""
        node = {
            "pname": "safe-pkg",
            "drv_path": "/nix/store/abc-safe-1.0.drv",
            "children": [],
        }
        html = tree_node_html(node, {})
        self.assertIn("sev-NONE", html)
        self.assertIn("NONE", html)

    def test_recursive_children(self):
        """Children are rendered recursively."""
        node = {
            "pname": "parent",
            "drv_path": "/nix/store/abc-parent-1.0.drv",
            "children": [
                {
                    "pname": "child1",
                    "drv_path": "/nix/store/def-child1-1.0.drv",
                    "children": [
                        {
                            "pname": "grandchild",
                            "drv_path": "/nix/store/ghi-gc-1.0.drv",
                            "children": [],
                        }
                    ],
                }
            ],
        }
        html = tree_node_html(node, {}, expanded=True)
        self.assertIn("parent", html)
        self.assertIn("child1", html)
        self.assertIn("grandchild", html)


class TestTreeHtml(unittest.TestCase):
    """Tests for tree_html template."""

    def test_returns_inner_html(self):
        """tree_html returns inner HTML (not full page)."""
        html = tree_html(1, {})
        self.assertIn("Dependency Tree", html)
        self.assertIn("hx-get", html)
        self.assertNotIn("<!DOCTYPE html>", html)

    def test_base_html_returns_full_page(self):
        """base_html returns a full HTML page."""
        html = base_html("Title", tree_html(1, {}))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)


if __name__ == "__main__":
    unittest.main()
