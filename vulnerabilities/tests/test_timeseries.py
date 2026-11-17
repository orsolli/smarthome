"""Tests for core/timeseries module."""

import os
import sqlite3
import tempfile
import unittest
from datetime import timedelta

from core import database
from core import timeseries


class TestTimeseries(unittest.TestCase):
    """Tests for timeseries query functions."""

    def setUp(self):
        """Create a temporary database with test data."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.conn = database.init_db(self.db_path)

        # Insert a scan
        scan_id = database.insert_scan(self.conn, "/run/current-system")
        self.scan_id = scan_id

        # Insert some vulnerability events
        database.insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/abc-Diff-9.99.0.drv", "CRITICAL"
        )
        database.insert_vulnerability_event(
            self.conn, scan_id, "ShellCheck", "/nix/store/def-ShellCheck-9.99.0.drv", "HIGH"
        )
        database.insert_vulnerability_event(
            self.conn, scan_id, "ed", "/nix/store/ghi-ed-9.99.0.drv", "MEDIUM"
        )

        # Insert a second scan
        scan_id2 = database.insert_scan(self.conn, "/run/current-system")
        database.insert_vulnerability_event(
            self.conn, scan_id2, "Diff", "/nix/store/abc-Diff-9.99.0.drv", "CRITICAL"
        )
        database.insert_vulnerability_event(
            self.conn, scan_id2, "vim", "/nix/store/jkl-vim-9.1.drv", "LOW"
        )

        self.conn.commit()

    def tearDown(self):
        """Close connection and remove temp file."""
        try:
            self.conn.close()
        except Exception:
            pass
        try:
            os.close(self.db_fd)
        except Exception:
            pass
        try:
            os.unlink(self.db_path)
        except Exception:
            pass

    def test_get_timeseries_for_package(self):
        """Test querying timeseries for a single package."""
        data = timeseries.get_timeseries_for_package(self.conn, "Diff")
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["package_name"], "Diff")
        self.assertEqual(data[0]["severity"], "CRITICAL")
        self.assertEqual(data[1]["severity"], "CRITICAL")

    def test_get_timeseries_for_package_no_match(self):
        """Test querying timeseries for a package not in DB."""
        data = timeseries.get_timeseries_for_package(self.conn, "nonexistent")
        self.assertEqual(len(data), 0)

    def test_get_timeseries_for_all_packages(self):
        """Test querying timeseries for all packages."""
        data = timeseries.get_timeseries_for_all_packages(self.conn)
        self.assertEqual(len(data), 5)
        packages = {row["package_name"] for row in data}
        self.assertIn("Diff", packages)
        self.assertIn("ShellCheck", packages)
        self.assertIn("ed", packages)
        self.assertIn("vim", packages)

    def test_get_timeseries_with_since_filter(self):
        """Test timeseries with since filter."""
        data = timeseries.get_timeseries_for_package(
            self.conn, "Diff", since="2020-01-01"
        )
        self.assertEqual(len(data), 2)

    def test_get_timeseries_with_until_filter(self):
        """Test timeseries with until filter."""
        data = timeseries.get_timeseries_for_package(
            self.conn, "Diff", until="2030-01-01"
        )
        self.assertEqual(len(data), 2)

    def test_get_timeseries_with_both_filters(self):
        """Test timeseries with both since and until filters."""
        data = timeseries.get_timeseries_for_package(
            self.conn, "Diff", since="2020-01-01", until="2030-01-01"
        )
        self.assertEqual(len(data), 2)

    def test_get_aggregated_severity(self):
        """Test severity aggregation for a package."""
        agg = timeseries.get_aggregated_severity(self.conn, self.scan_id, "Diff")
        self.assertEqual(agg["max_severity"], "CRITICAL")
        self.assertEqual(agg["scan_count"], 1)
        self.assertEqual(agg["latest_severity"], "CRITICAL")

    def test_get_aggregated_severity_no_match(self):
        """Test aggregation for a package not in a scan."""
        agg = timeseries.get_aggregated_severity(self.conn, self.scan_id, "nonexistent")
        self.assertEqual(agg["max_severity"], "LOW")
        self.assertEqual(agg["scan_count"], 0)


class TestSubtreeTimeseries(unittest.TestCase):
    """Tests for get_subtree_timeseries (tree-aware aggregation)."""

    def setUp(self):
        """Create a temp DB with a root -> ShellCheck -> Diff dependency tree."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.conn = database.init_db(self.db_path)

        self.scan1 = database.insert_scan(self.conn, "./result")
        self.scan2 = database.insert_scan(self.conn, "./result")

        root = database.insert_dependency_node(
            self.conn, self.scan1, "system", "/nix/store/system.drv"
        )
        sc = database.insert_dependency_node(
            self.conn, self.scan1, "ShellCheck", "/nix/store/sc.drv", parent_id=root
        )
        database.insert_dependency_node(
            self.conn, self.scan1, "Diff", "/nix/store/diff.drv", parent_id=sc
        )
        database.insert_dependency_node(
            self.conn, self.scan1, "gzip", "/nix/store/gzip.drv", parent_id=root
        )

        database.insert_vulnerability_event(
            self.conn, self.scan1, "system", "/nix/store/system.drv", "LOW"
        )
        database.insert_vulnerability_event(
            self.conn, self.scan1, "ShellCheck", "/nix/store/sc.drv", "HIGH"
        )
        database.insert_vulnerability_event(
            self.conn, self.scan2, "Diff", "/nix/store/diff.drv", "CRITICAL"
        )
        self.conn.commit()

    def tearDown(self):
        try:
            self.conn.close()
        except Exception:
            pass
        try:
            os.close(self.db_fd)
        except Exception:
            pass
        try:
            os.unlink(self.db_path)
        except Exception:
            pass

    def test_root_subtree_aggregates_children(self):
        """Root subtree inherits the highest severity from any descendant."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, "/nix/store/system.drv"
        )
        self.assertEqual(len(data), 2)
        severities = {row["scan_id"]: row["severity"] for row in data}
        self.assertEqual(severities[self.scan1], "HIGH")  # LOW (self) vs HIGH (child)
        self.assertEqual(severities[self.scan2], "CRITICAL")  # Diff is a descendant

    def test_leaf_subtree_is_itself(self):
        """A subtree with no vulnerable descendants yields nothing."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, "/nix/store/gzip.drv"
        )
        self.assertEqual(data, [])

    def test_subtree_of_vulnerable_child(self):
        """Diff alone is vulnerable only in scan 2."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, "/nix/store/diff.drv"
        )
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["severity"], "CRITICAL")
        self.assertEqual(data[0]["scan_id"], self.scan2)

    def test_unknown_drv_path(self):
        """A drv path not in the tree yields an empty timeline."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, "/nix/store/unknown.drv"
        )
        self.assertEqual(data, [])

    def test_tree_timelines_cover_every_node(self):
        """One pass returns the aggregated timeline for every node."""
        timelines = timeseries.get_tree_subtree_timelines(self.conn, self.scan1)
        self.assertIn("/nix/store/system.drv", timelines)
        self.assertIn("/nix/store/sc.drv", timelines)
        self.assertIn("/nix/store/diff.drv", timelines)
        # gzip has no vulnerable descendants, so it is absent
        self.assertNotIn("/nix/store/gzip.drv", timelines)

    def test_tree_timelines_bubble_children_up(self):
        """Ancestors inherit the worst severity of their subtree."""
        timelines = timeseries.get_tree_subtree_timelines(self.conn, self.scan1)
        root = timelines["/nix/store/system.drv"]
        self.assertEqual(len(root), 2)
        self.assertEqual(root[0]["severity"], "HIGH")  # self LOW, child HIGH
        self.assertEqual(root[1]["severity"], "CRITICAL")  # Diff is a descendant

    def test_scan_window_spans_all_scans(self):
        """The chart window covers every scan, padded by a day."""
        start, end = timeseries.get_scan_window(self.conn)
        cursor = self.conn.execute(
            "SELECT MIN(timestamp), MAX(timestamp) FROM scans"
        )
        lowest, highest = cursor.fetchone()
        self.assertEqual(start, timeseries._parse_iso(lowest) - timedelta(days=1))
        self.assertEqual(end, timeseries._parse_iso(highest) + timedelta(days=1))

    def test_scan_window_with_no_scans(self):
        """An empty database yields a degenerate window instead of crashing."""
        empty_fd, empty_path = tempfile.mkstemp(suffix=".db")
        os.close(empty_fd)
        conn = database.init_db(empty_path)
        try:
            start, end = timeseries.get_scan_window(conn)
            self.assertLess(start, end)
        finally:
            conn.close()
            os.unlink(empty_path)


if __name__ == "__main__":
    unittest.main()
