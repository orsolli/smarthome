"""Tests for database module."""

import os
import tempfile
import unittest

from core.database import (
    init_db,
    insert_scan,
    insert_vulnerability_event,
    insert_dependency_node,
    get_vulnerabilities_since,
    get_dependency_tree_for_scan,
)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        self.conn = init_db(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_init_db_creates_tables(self):
        """Database initializes with all required tables."""
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        self.assertIn("scans", tables)
        self.assertIn("vulnerability_events", tables)
        self.assertIn("dependency_tree", tables)

    def test_insert_scan_returns_id(self):
        """Inserting a scan returns a valid ID."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        self.assertEqual(scan_id, 1)

    def test_insert_vulnerability_event_returns_id(self):
        """Inserting a vulnerability event returns a valid ID."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        event_id = insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/Diff.drv", "HIGH"
        )
        self.assertEqual(event_id, 1)

    def test_insert_dependency_node_returns_id(self):
        """Inserting a dependency node returns a valid ID."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        node_id = insert_dependency_node(
            self.conn, scan_id, "nixos-system", "/nix/store/system.drv"
        )
        self.assertEqual(node_id, 1)

    def test_get_vulnerabilities_since_returns_events(self):
        """Querying vulnerabilities since a date returns correct events."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/Diff.drv", "HIGH"
        )
        vulns = get_vulnerabilities_since(self.conn, "2020-01-01")
        self.assertEqual(len(vulns), 1)
        self.assertEqual(vulns[0]["package_name"], "Diff")
        self.assertEqual(vulns[0]["severity"], "HIGH")

    def test_get_vulnerabilities_since_with_until(self):
        """Querying with until bounds works correctly."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/Diff.drv", "HIGH"
        )
        vulns = get_vulnerabilities_since(self.conn, "2020-01-01", "2030-01-01")
        self.assertEqual(len(vulns), 1)

    def test_get_vulnerabilities_since_filters_outside_range(self):
        """Querying with a past 'since' returns no results for future events."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/Diff.drv", "HIGH"
        )
        vulns = get_vulnerabilities_since(self.conn, "2030-01-01")
        self.assertEqual(len(vulns), 0)

    def test_get_dependency_tree_for_scan(self):
        """Querying dependency tree for a scan returns correct nodes."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        node_id = insert_dependency_node(
            self.conn, scan_id, "nixos-system", "/nix/store/system.drv"
        )
        tree = get_dependency_tree_for_scan(self.conn, scan_id)
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["package_name"], "nixos-system")
        self.assertEqual(tree[0]["drv_path"], "/nix/store/system.drv")


if __name__ == "__main__":
    unittest.main()
