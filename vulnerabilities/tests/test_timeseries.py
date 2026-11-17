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
        self.assertEqual(agg["max_severity"], "NONE")
        self.assertEqual(agg["scan_count"], 0)
        self.assertEqual(agg["latest_severity"], "NONE")


class TestSubtreeTimeseries(unittest.TestCase):
    """Tests for subtree timelines keyed by node identity, not drv path."""

    HASH = "abcdefghijklmnopqrstuvwxyz01234567"

    def setUp(self):
        """Two scans of the same target with a root -> ShellCheck -> Diff tree."""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.conn = database.init_db(self.db_path)

        def drv(name, version):
            return f"/nix/store/{self.HASH}-{name}-{version}.drv"

        self.system_drv = "/nix/store/%s-nixos-system.drv" % self.HASH
        self.sc_drv = drv("ShellCheck", "9.99.0")
        self.diff1_drv = drv("Diff", "9.99.0")
        self.diff2_drv = drv("Diff", "1.0.3")
        self.gzip_drv = drv("gzip", "1.10")

        self.scan1 = database.insert_scan(self.conn, "./result")
        self.scan2 = database.insert_scan(self.conn, "./result")
        self.scan_other = database.insert_scan(self.conn, "./other-target")

        for scan_id, diff_drv, diff_version in (
            (self.scan1, self.diff1_drv, "9.99.0"),
            (self.scan2, self.diff2_drv, "1.0.3"),
        ):
            root = database.insert_dependency_node(
                self.conn, scan_id, "nixos-system", self.system_drv,
                lineage="./result",
            )
            sc = database.insert_dependency_node(
                self.conn, scan_id, "ShellCheck", self.sc_drv, parent_id=root,
                version="9.99.0", lineage="./result/ShellCheck",
            )
            database.insert_dependency_node(
                self.conn, scan_id, "Diff", diff_drv, parent_id=sc,
                version=diff_version, lineage="./result/ShellCheck/Diff",
            )
            database.insert_dependency_node(
                self.conn, scan_id, "gzip", self.gzip_drv, parent_id=root,
                version="1.10", lineage="./result/gzip",
            )

        # A scan of a different target: it must never enter these timelines.
        other_root = database.insert_dependency_node(
            self.conn, self.scan_other, "nixos-system", self.system_drv,
            lineage="./other-target",
        )
        database.insert_dependency_node(
            self.conn, self.scan_other, "Diff", self.diff2_drv, parent_id=other_root,
            version="1.0.3", lineage="./other-target/Diff",
        )

        database.insert_vulnerability_event(
            self.conn, self.scan1, "nixos-system", self.system_drv, "LOW"
        )
        database.insert_vulnerability_event(
            self.conn, self.scan1, "ShellCheck", self.sc_drv, "HIGH"
        )
        database.insert_vulnerability_event(
            self.conn, self.scan2, "Diff", self.diff2_drv, "CRITICAL"
        )
        database.insert_vulnerability_event(
            self.conn, self.scan_other, "Diff", self.diff2_drv, "CRITICAL"
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
            self.conn, self.scan1, self.system_drv
        )
        self.assertEqual(len(data), 2)
        severities = {row["scan_id"]: row["severity"] for row in data}
        self.assertEqual(severities[self.scan1], "HIGH")  # LOW (self) vs HIGH (child)
        self.assertEqual(severities[self.scan2], "CRITICAL")  # Diff is a descendant

    def test_clean_scans_are_recorded_as_none(self):
        """A node present in a scan without vulnerabilities gets an explicit NONE."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, self.gzip_drv
        )
        self.assertEqual([row["severity"] for row in data], ["NONE", "NONE"])

    def test_subtree_of_vulnerable_child(self):
        """Diff is clean in scan 1 and vulnerable in scan 2."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, self.diff1_drv
        )
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["severity"], "NONE")
        self.assertEqual(data[1]["severity"], "CRITICAL")
        self.assertEqual(data[1]["scan_id"], self.scan2)

    def test_versions_of_matched_nodes_are_reported(self):
        """Each entry carries the version the node had in that scan."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, self.diff1_drv
        )
        versions = {row["scan_id"]: row["version"] for row in data}
        self.assertEqual(versions[self.scan1], "9.99.0")
        self.assertEqual(versions[self.scan2], "1.0.3")

    def test_unknown_drv_path(self):
        """A drv path not in the tree yields an empty timeline."""
        data = timeseries.get_subtree_timeseries(
            self.conn, self.scan1, "/nix/store/unknown.drv"
        )
        self.assertEqual(data, [])

    def test_tree_timelines_cover_every_node(self):
        """One pass returns the aggregated timeline for every node."""
        timelines = timeseries.get_tree_subtree_timelines(self.conn, self.scan1)
        self.assertEqual(len(timelines), 4)
        for drv_path in (self.system_drv, self.sc_drv, self.diff1_drv, self.gzip_drv):
            self.assertIn(drv_path, timelines)

    def test_tree_timelines_bubble_children_up(self):
        """Ancestors inherit the worst severity of their subtree."""
        timelines = timeseries.get_tree_subtree_timelines(self.conn, self.scan1)
        root = timelines[self.system_drv]
        self.assertEqual(len(root), 2)
        self.assertEqual(root[0]["severity"], "HIGH")  # self LOW, child HIGH
        self.assertEqual(root[1]["severity"], "CRITICAL")  # Diff is a descendant

    def test_scans_of_other_targets_are_excluded(self):
        """Only scans of the same target are compared."""
        timelines = timeseries.get_tree_subtree_timelines(self.conn, self.scan1)
        scan_ids = {row["scan_id"] for entry in timelines.values() for row in entry}
        self.assertEqual(scan_ids, {self.scan1, self.scan2})

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


class TestCrossScanMatching(unittest.TestCase):
    """The fallback rules that recognise a node in an older scan of a target."""

    HASH = "abcdefghijklmnopqrstuvwxyz01234567"

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.conn = database.init_db(self.db_path)

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

    def _scan(self, target, specs):
        """Insert one scan. specs: (name, version, lineage[, parent_index]).

        Returns (scan_id, {(name, version): drv_path}).
        """
        scan_id = database.insert_scan(self.conn, target)
        drv_paths: dict[tuple[str, str], str] = {}
        node_ids: list[int] = []
        for index, spec in enumerate(specs):
            name, version, lineage = spec[:3]
            parent_index = spec[3] if len(spec) > 3 else None
            drv = (
                f"/nix/store/{self.HASH}-{name}-{version}.drv"
                if version
                else f"/nix/store/{self.HASH}-{name}.drv"
            )
            node_ids.append(
                database.insert_dependency_node(
                    self.conn,
                    scan_id,
                    name,
                    drv,
                    parent_id=node_ids[parent_index] if parent_index is not None else None,
                    version=version,
                    lineage=lineage,
                )
            )
            drv_paths[(name, version)] = drv
        return scan_id, drv_paths

    def _severity_of(self, timelines, drv):
        return [entry["severity"] for entry in timelines[drv]]

    def test_same_lineage_and_version_matches(self):
        older, older_drv = self._scan("./result", [("gcc", "9.99.0", "./result/strata/gcc")])
        current, current_drv = self._scan("./result", [("gcc", "9.99.0", "./result/strata/gcc")])
        database.insert_vulnerability_event(
            self.conn, older, "gcc", older_drv[("gcc", "9.99.0")], "HIGH"
        )
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        self.assertEqual(self._severity_of(timelines, current_drv[("gcc", "9.99.0")]), ["HIGH", "NONE"])

    def test_lineage_match_survives_a_version_bump(self):
        older, older_drv = self._scan("./result", [("gcc", "9.99.0", "./result/strata/gcc")])
        current, current_drv = self._scan("./result", [("gcc", "15.4.0", "./result/strata/gcc")])
        database.insert_vulnerability_event(
            self.conn, older, "gcc", older_drv[("gcc", "9.99.0")], "HIGH"
        )
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        entries = timelines[current_drv[("gcc", "15.4.0")]]
        self.assertEqual([e["severity"] for e in entries], ["HIGH", "NONE"])
        self.assertEqual([e["version"] for e in entries], ["9.99.0", "15.4.0"])

    def test_moved_package_matches_by_name_and_version(self):
        older, _ = self._scan("./result", [("gcc", "9.99.0", "./result/libiberty/gcc")])
        current, current_drv = self._scan("./result", [("gcc", "9.99.0", "./result/strata/gcc")])
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        self.assertEqual(len(timelines[current_drv[("gcc", "9.99.0")]]), 2)

    def test_unique_name_matches_across_a_version_change(self):
        older, older_drv = self._scan("./result", [("boost", "1.89.0", "./result/a/boost")])
        current, current_drv = self._scan("./result", [("boost", "1.91.0", "./result/b/boost")])
        database.insert_vulnerability_event(
            self.conn, older, "boost", older_drv[("boost", "1.89.0")], "MEDIUM"
        )
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        self.assertEqual(self._severity_of(timelines, current_drv[("boost", "1.91.0")]), ["MEDIUM", "NONE"])

    def test_duplicate_name_without_a_lineage_match_has_no_history(self):
        self._scan("./result", [
            ("gcc", "1.0", "./result/a/gcc"),
            ("gcc", "2.0", "./result/b/gcc"),
        ])
        current, current_drv = self._scan("./result", [("gcc", "3.0", "./result/c/gcc")])
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        self.assertEqual(self._severity_of(timelines, current_drv[("gcc", "3.0")]), ["NONE"])

    def test_identical_name_and_version_match_even_when_duplicated(self):
        older, older_drv = self._scan("./result", [("gcc", "9.99.0", "./result/strata/gcc")])
        current, current_drv = self._scan("./result", [
            ("gcc", "9.99.0", "./result/a/gcc"),
            ("gcc", "9.99.0", "./result/b/gcc"),
        ])
        database.insert_vulnerability_event(
            self.conn, older, "gcc", older_drv[("gcc", "9.99.0")], "HIGH"
        )
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        for drv in current_drv.values():
            self.assertEqual(self._severity_of(timelines, drv), ["HIGH", "NONE"])

    def test_severity_bubbles_up_to_the_matched_ancestor(self):
        older, older_drv = self._scan("./result", [
            ("system", "", "./result"),
            ("curl", "8.5.0", "./result/system-path/curl", 0),
        ])
        current, current_drv = self._scan("./result", [
            ("system", "", "./result"),
            ("curl", "8.6.0", "./result/system-path/curl", 0),
        ])
        database.insert_vulnerability_event(
            self.conn, older, "curl", older_drv[("curl", "8.5.0")], "HIGH"
        )
        timelines = timeseries.get_tree_subtree_timelines(self.conn, current)
        self.assertEqual(self._severity_of(timelines, current_drv[("system", "")]), ["HIGH", "NONE"])
        self.assertEqual(self._severity_of(timelines, current_drv[("curl", "8.6.0")]), ["HIGH", "NONE"])


if __name__ == "__main__":
    unittest.main()
