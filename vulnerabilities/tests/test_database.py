"""Tests for database module."""

import os
import sqlite3
import tempfile
import unittest

from core.database import (
    init_db,
    insert_scan,
    insert_vulnerability_event,
    insert_dependency_node,
    update_dependency_node,
    get_vulnerabilities_since,
    get_dependency_tree_for_scan,
    get_scans_for_target,
    list_targets,
    backfill_identities,
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

    def test_insert_scan_keeps_a_backfilled_timestamp(self):
        """A generation scan is dated when it ran, not when it was replayed."""
        scan_id = insert_scan(self.conn, "/run/current-system", "2025-10-14T08:21:00")
        row = self.conn.execute(
            "SELECT timestamp FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
        self.assertEqual(row[0], "2025-10-14T08:21:00")

    def test_insert_vulnerability_event_returns_id(self):
        """Inserting a vulnerability event returns a valid ID."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        event_id = insert_vulnerability_event(
            self.conn, scan_id, "Diff", "/nix/store/Diff.drv", "HIGH"
        )
        self.assertEqual(event_id, 1)

    def test_insert_vulnerability_event_keeps_the_scan_timestamp(self):
        """Events of a backfilled generation are not dated today."""
        scan_id = insert_scan(self.conn, "/run/current-system", "2025-10-14T08:21:00")
        insert_vulnerability_event(
            self.conn,
            scan_id,
            "Diff",
            "/nix/store/Diff.drv",
            "HIGH",
            timestamp="2025-10-14T08:21:00",
        )
        row = self.conn.execute(
            "SELECT timestamp FROM vulnerability_events WHERE scan_id = ?", (scan_id,)
        ).fetchone()
        self.assertEqual(row[0], "2025-10-14T08:21:00")

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


class TestUpdateDependencyNode(unittest.TestCase):
    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        self.conn = init_db(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_update_raises_for_nonexistent_id(self):
        """update_dependency_node raises ValueError for non-existent ID."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        with self.assertRaises(ValueError):
            update_dependency_node(self.conn, 999, scan_id, "pkg", "/drv")

    def test_update_updates_all_fields(self):
        """update_dependency_node updates all provided fields."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        node_id = insert_dependency_node(
            self.conn, scan_id, "old-pkg", "/nix/store/old.drv"
        )
        update_dependency_node(
            self.conn, node_id, scan_id, "new-pkg", "/nix/store/new.drv"
        )
        tree = get_dependency_tree_for_scan(self.conn, scan_id)
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["package_name"], "new-pkg")
        self.assertEqual(tree[0]["drv_path"], "/nix/store/new.drv")

    def test_update_preserves_unprovided_fields(self):
        """update_dependency_node preserves fields not provided."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        node_id = insert_dependency_node(
            self.conn, scan_id, "pkg", "/nix/store/p.drv",
            parent_id=5, child_id=10, vulnerability_event_id=3
        )
        update_dependency_node(self.conn, node_id, scan_id, "pkg", "/nix/store/p.drv",
                               child_id=20)
        tree = get_dependency_tree_for_scan(self.conn, scan_id)
        self.assertEqual(tree[0]["parent_id"], 5)
        self.assertEqual(tree[0]["child_id"], 20)
        self.assertEqual(tree[0]["vulnerability_event_id"], 3)


class TestNodeIdentity(unittest.TestCase):
    """Version, lineage and target scoping written by the database layer."""

    HASH = "abcdefghijklmnopqrstuvwxyz01234567"

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        self.conn = init_db(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_version_is_derived_from_the_drv_path(self):
        scan_id = insert_scan(self.conn, "/run/current-system")
        node_id = insert_dependency_node(
            self.conn,
            scan_id,
            "glibc-2.42",
            f"/nix/store/{self.HASH}-glibc-9.99-11.drv",
        )
        node = get_dependency_tree_for_scan(self.conn, scan_id)[0]
        self.assertEqual(node["version"], "9.99-11")
        self.assertEqual(node["lineage"], None)
        self.assertEqual(node["id"], node_id)

    def test_scans_are_grouped_by_target(self):
        a = insert_scan(self.conn, "/run/current-system")
        insert_scan(self.conn, "./result")
        b = insert_scan(self.conn, "/run/current-system")
        scans = get_scans_for_target(self.conn, a)
        self.assertEqual([scan["id"] for scan in scans], [a, b])
        self.assertEqual(scans[0]["target"], "/run/current-system")

    def test_scanned_path_records_the_generation_scanned(self):
        """`target` is the identity, `scanned_path` the derivation actually read."""
        scan_id = insert_scan(
            self.conn,
            "/run/current-system",
            timestamp="2024-11-01T15:48:40",
            scanned_path="/nix/var/nix/profiles/system-3-link",
        )
        row = self.conn.execute(
            "SELECT target, scanned_path FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
        self.assertEqual(
            (row["target"], row["scanned_path"]),
            ("/run/current-system", "/nix/var/nix/profiles/system-3-link"),
        )

    def test_scanned_path_defaults_to_the_target(self):
        scan_id = insert_scan(self.conn, "./result")
        row = self.conn.execute(
            "SELECT scanned_path FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
        self.assertEqual(row[0], "./result")

    def test_scans_for_target_carry_their_scanned_path(self):
        a = insert_scan(
            self.conn, "/run/current-system",
            scanned_path="/nix/var/nix/profiles/system-2-link",
        )
        insert_scan(self.conn, "./other")
        b = insert_scan(
            self.conn, "/run/current-system",
            scanned_path="/nix/var/nix/profiles/system-3-link",
        )
        scans = get_scans_for_target(self.conn, a)
        self.assertEqual([scan["id"] for scan in scans], [a, b])
        self.assertEqual(
            [scan["scanned_path"] for scan in scans],
            ["/nix/var/nix/profiles/system-2-link", "/nix/var/nix/profiles/system-3-link"],
        )

    def test_scans_for_target_can_be_cut_at_a_date(self):
        a = insert_scan(self.conn, "/run/current-system", timestamp="2024-01-01T00:00:00")
        insert_scan(self.conn, "/run/current-system", timestamp="2024-06-01T00:00:00")
        insert_scan(self.conn, "./other", timestamp="2024-09-01T00:00:00")
        scans = get_scans_for_target(self.conn, a, since="2024-03-01T00:00:00")
        self.assertEqual([scan["timestamp"] for scan in scans], ["2024-06-01T00:00:00"])

    def test_backfill_computes_lineages_for_legacy_rows(self):
        """Rows written before node identity existed get version and lineage."""
        scan_id = insert_scan(self.conn, "/run/current-system")
        root = insert_dependency_node(
            self.conn, scan_id, "nixos-system", "/nix/store/system.drv"
        )
        stdenv = insert_dependency_node(
            self.conn, scan_id, "stdenv-linux", "/nix/store/stdenv.drv", parent_id=root
        )
        gcc = insert_dependency_node(
            self.conn, scan_id, "gcc", f"/nix/store/{self.HASH}-gcc-4.6.4.drv",
            parent_id=stdenv,
        )
        insert_vulnerability_event(
            self.conn, scan_id, "gcc", f"/nix/store/{self.HASH}-gcc-4.6.4.drv", "HIGH"
        )

        filled = backfill_identities(self.conn)
        self.assertEqual(filled, 1)

        nodes = {n["id"]: n for n in get_dependency_tree_for_scan(self.conn, scan_id)}
        self.assertEqual(nodes[root]["lineage"], "/run/current-system")
        self.assertEqual(nodes[stdenv]["lineage"], "/run/current-system/stdenv-linux")
        self.assertEqual(nodes[gcc]["lineage"], "/run/current-system/stdenv-linux/gcc")
        self.assertEqual(nodes[gcc]["version"], "4.6.4")

        event = self.conn.execute(
            "SELECT version FROM vulnerability_events WHERE package_name = 'gcc'"
        ).fetchone()
        self.assertEqual(event[0], "4.6.4")

        # Idempotent: a second pass changes nothing.
        self.assertEqual(backfill_identities(self.conn), 0)
        again = {n["id"]: n for n in get_dependency_tree_for_scan(self.conn, scan_id)}
        self.assertEqual(again[gcc]["lineage"], nodes[gcc]["lineage"])


class TestTargetList(unittest.TestCase):
    """One row per scanned identity, most recently scanned first."""

    HASH = "abcdefghijklmnopqrstuvwxyz01234567"

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.conn = init_db(self.db_path)

        self.old = insert_scan(
            self.conn, "/run/current-system",
            timestamp="2024-10-14T08:21:14",
            scanned_path="/nix/var/nix/profiles/system-2-link",
        )
        self.latest = insert_scan(
            self.conn, "/run/current-system",
            timestamp="2024-11-17T19:16:29",
            scanned_path="/nix/var/nix/profiles/system-5-link",
        )
        self.dotfiles = insert_scan(
            self.conn, "~/.dotfiles/result-example",
            timestamp="2024-11-19T10:00:00",
        )

        insert_vulnerability_event(
            self.conn, self.old, "perl", f"/nix/store/{self.HASH}-perl-5.34.drv", "CRITICAL"
        )
        insert_vulnerability_event(
            self.conn, self.latest, "jq", f"/nix/store/{self.HASH}-jq-1.7.drv", "MEDIUM"
        )
        insert_vulnerability_event(
            self.conn, self.dotfiles, "fontforge",
            f"/nix/store/{self.HASH}-fontforge-2.4.drv", "HIGH"
        )

    def tearDown(self):
        self.conn.close()
        try:
            os.close(self.db_fd)
        except Exception:
            pass
        os.unlink(self.db_path)

    def test_each_target_is_listed_once(self):
        targets = list_targets(self.conn)
        self.assertEqual(
            [target["target"] for target in targets],
            ["~/.dotfiles/result-example", "/run/current-system"],
        )

    def test_counts_and_dates_of_a_target(self):
        system = next(t for t in list_targets(self.conn) if t["target"] == "/run/current-system")
        self.assertEqual(system["scan_count"], 2)
        self.assertEqual(system["first_scan"], "2024-10-14T08:21:14")
        self.assertEqual(system["last_scan"], "2024-11-17T19:16:29")
        self.assertEqual(system["latest_scan_id"], self.latest)

    def test_worst_severity_is_that_of_the_latest_scan(self):
        """The list is a current status, not the history of every generation."""
        system = next(t for t in list_targets(self.conn) if t["target"] == "/run/current-system")
        self.assertEqual(system["worst_severity"], "MEDIUM")

    def test_a_target_with_no_vulnerabilities_is_clean(self):
        insert_scan(self.conn, "./empty-result", timestamp="2024-11-20T00:00:00")
        empty = next(t for t in list_targets(self.conn) if t["target"] == "./empty-result")
        self.assertEqual(empty["worst_severity"], "NONE")
        self.assertEqual(empty["scan_count"], 1)

    def test_a_database_without_scanned_path_is_upgraded(self):
        """Databases created before the column exists keep their rows."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        legacy = sqlite3.connect(path)
        legacy.execute(
            "CREATE TABLE scans (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp TEXT NOT NULL, target TEXT NOT NULL)"
        )
        legacy.execute(
            "INSERT INTO scans (timestamp, target) VALUES ('2024-10-14T08:21:14', '/run/current-system')"
        )
        legacy.commit()
        legacy.close()

        conn = init_db(path)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(scans)")}
        self.assertIn("scanned_path", columns)
        row = conn.execute("SELECT target FROM scans").fetchone()
        self.assertEqual(row[0], "/run/current-system")
        conn.close()
        os.unlink(path)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
