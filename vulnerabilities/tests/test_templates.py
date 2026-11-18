"""Tests for app/templates.py."""

import unittest

from app.templates import (
    base_html,
    sidebar_html,
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


class TestSidebar(unittest.TestCase):
    """Navigation column: one row per target, plus the window chips."""

    TARGETS = [
        {
            "target": "/run/current-system",
            "scan_count": 18,
            "first_scan": "2024-10-14T08:21:14",
            "last_scan": "2024-11-17T19:16:29",
            "latest_scan_id": 18,
            "worst_severity": "HIGH",
        },
        {
            "target": "./result",
            "scan_count": 1,
            "first_scan": "2024-11-19T10:00:00",
            "last_scan": "2024-11-19T10:00:00",
            "latest_scan_id": 19,
            "worst_severity": "NONE",
        },
    ]
    SCAN = {
        "id": 18,
        "timestamp": "2024-11-17T19:16:29",
        "target": "/run/current-system",
        "scanned_path": "/nix/var/nix/profiles/system-5-link",
    }

    def test_each_target_links_to_its_latest_scan(self):
        html = sidebar_html(self.TARGETS)
        self.assertIn('<a href="/scan/18">/run/current-system</a>', html)
        self.assertIn("18 scans · 2024-11-17", html)
        self.assertIn("1 scan · 2024-11-19", html)

    def test_a_target_is_coloured_by_its_latest_scan(self):
        html = sidebar_html(self.TARGETS)
        self.assertIn('class="severity-dot sev-HIGH"', html)
        self.assertIn('class="severity-dot sev-NONE"', html)

    def test_an_empty_database_says_so(self):
        self.assertIn("No scans yet", sidebar_html([]))

    def test_chips_offer_7_30_90_days_and_the_whole_history(self):
        html = sidebar_html(self.TARGETS, self.SCAN, days=30)
        for label in ("7d", "30d", "90d", "all"):
            self.assertIn(f">{label}</a>", html)
        self.assertIn('class="chip active" href="/scan/18?days=30"', html)
        self.assertIn('class="chip" href="/scan/18"', html)

    def test_the_generation_scanned_is_named(self):
        html = sidebar_html(self.TARGETS, self.SCAN)
        self.assertIn("system-5-link", html)
        self.assertIn("2024-11-17 19:16", html)

    def test_a_scan_without_a_scanned_path_falls_back_to_the_target(self):
        scan = dict(self.SCAN, scanned_path=None)
        html = sidebar_html(self.TARGETS, scan)
        self.assertIn("<code>/run/current-system</code>", html)

    def test_the_home_page_has_no_window_controls(self):
        self.assertNotIn("window-chips", sidebar_html(self.TARGETS))


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
        html = tree_html(1)
        self.assertIn("Dependency Tree", html)
        self.assertIn("hx-get", html)
        self.assertNotIn("<!DOCTYPE html>", html)

    def test_tree_container_loads_on_page_load(self):
        """The tree itself is fetched when the page loads."""
        html = tree_html(42)
        self.assertIn('id="tree-root"', html)
        self.assertIn('hx-get="/api/tree/42"', html)
        self.assertIn('hx-trigger="load"', html)
        # Bars are emitted by /api/tree, not here, so they arrive with the tree
        self.assertNotIn('hx-get="/api/bars/42"', html)

    def test_toggle_node_triggers_children(self):
        """Expanding a node fires node-expanded on its children container."""
        html = tree_html(42)
        self.assertIn("toggleNode", html)
        self.assertIn("node-expanded", html)

    def test_the_window_is_part_of_the_tree_url(self):
        html = tree_html(42, days=7)
        self.assertIn('hx-get="/api/tree/42?days=7"', html)
        self.assertNotIn('hx-get="/api/tree/42"', html)

    def test_base_html_returns_full_page(self):
        """base_html returns a full HTML page."""
        html = base_html("Title", tree_html(1))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)


if __name__ == "__main__":
    unittest.main()
