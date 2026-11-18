"""Tests for app/templates.py."""

import unittest

from app.templates import (
    base_html,
    node_dom_id,
    sidebar_html,
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
        html = base_html("Title", main=tree_html(1))
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)
        self.assertIn("</html>", html)


class TestNodeDomId(unittest.TestCase):
    """HTMX resolves an out-of-band swap with `#<id>`, so a node id carrying
    `+` or `=` never matches and the node keeps an empty timeline."""

    def test_characters_outside_a_css_identifier_are_flattened(self):
        self.assertEqual(
            node_dom_id("/nix/store/abc-webkitgtk-9.99.0+abi=1.0.drv"),
            "node-_nix_store_abc-webkitgtk-9_99_0_abi_1_0_drv",
        )
        self.assertEqual(
            node_dom_id("/nix/store/abc-xvfb-run-1+g87f6705.drv"),
            "node-_nix_store_abc-xvfb-run-1_g87f6705_drv",
        )

    def test_a_path_without_odd_characters_only_flattens_slashes_and_dots(self):
        self.assertEqual(
            node_dom_id("/nix/store/abc-firefox-125.0.drv"),
            "node-_nix_store_abc-firefox-125_0_drv",
        )
        self.assertEqual(
            node_dom_id("/nix/store/abc-system-path.drv"),
            "node-_nix_store_abc-system-path_drv",
        )


if __name__ == "__main__":
    unittest.main()
