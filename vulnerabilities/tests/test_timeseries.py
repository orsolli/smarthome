"""Tests for core/timeseries module."""

import os
import sqlite3
import tempfile
import unittest

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
            self.conn, scan_id, "Diff", "/nix/store/abc-Diff-1.0.2.drv", "CRITICAL"
        )
        database.insert_vulnerability_event(
            self.conn, scan_id, "ShellCheck", "/nix/store/def-ShellCheck-0.11.0.drv", "HIGH"
        )
        database.insert_vulnerability_event(
            self.conn, scan_id, "ed", "/nix/store/ghi-ed-1.22.5.drv", "MEDIUM"
        )

        # Insert a second scan
        scan_id2 = database.insert_scan(self.conn, "/run/current-system")
        database.insert_vulnerability_event(
            self.conn, scan_id2, "Diff", "/nix/store/abc-Diff-1.0.2.drv", "CRITICAL"
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


if __name__ == "__main__":
    unittest.main()
