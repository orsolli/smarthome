"""Tests for database module."""

import os
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


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
