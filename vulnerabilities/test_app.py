"""Tests for app module core logic."""

import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch

import app
import database


class TestRunScan(unittest.TestCase):
    """Tests for the run_scan function."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        app.DB_PATH = self.db_path

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    @patch.object(app, "show_derivation")
    @patch.object(app, "scan_vulnerabilities")
    @patch.object(app, "why_depends")
    @patch.object(app, "merge_dependency_trees")
    @patch.object(app, "normalize_tree")
    def test_scan_returns_results(
        self,
        mock_normalize,
        mock_merge,
        mock_why,
        mock_vuln,
        mock_derivation,
    ):
        """run_scan returns correct vulnerability results."""
        mock_derivation.return_value = {
            "/nix/store/test.drv": {}
        }
        mock_vuln.return_value = [
            {
                "pname": "Diff",
                "derivation": "/nix/store/Diff.drv",
                "cvssv3_basescore": {"CVE-2024-13278": 9.1},
            }
        ]
        mock_why.return_value = [
            {
                "pname": "nixos-system",
                "drv_path": "/nix/store/test.drv",
                "children": [
                    {
                        "pname": "Diff",
                        "drv_path": "/nix/store/Diff.drv",
                        "children": [],
                    }
                ],
            }
        ]
        mock_merge.return_value = {
            "pname": "nixos-system",
            "drv_path": "/nix/store/test.drv",
            "children": [
                {
                    "pname": "Diff",
                    "drv_path": "/nix/store/Diff.drv",
                    "children": [],
                }
            ],
        }
        mock_normalize.return_value = [
            {
                "package_name": "Diff",
                "drv_path": "/nix/store/Diff.drv",
                "severity": "CRITICAL",
            }
        ]

        result = app.run_scan("/run/current-system")

        self.assertEqual(result["vulnerabilities_found"], 1)
        self.assertEqual(result["vulnerabilities"][0]["package_name"], "Diff")
        self.assertEqual(result["vulnerabilities"][0]["severity"], "CRITICAL")
        self.assertEqual(result["target"], "/run/current-system")

    @patch.object(app, "show_derivation")
    def test_scan_no_derivation_returns_error(self, mock_derivation):
        """run_scan returns error when no derivation found."""
        mock_derivation.return_value = {}
        result = app.run_scan("/nonexistent")
        self.assertIn("error", result)

    @patch.object(app, "show_derivation")
    @patch.object(app, "scan_vulnerabilities")
    @patch.object(app, "why_depends")
    @patch.object(app, "merge_dependency_trees")
    @patch.object(app, "normalize_tree")
    def test_scan_stores_in_database(
        self,
        mock_normalize,
        mock_merge,
        mock_why,
        mock_vuln,
        mock_derivation,
    ):
        """run_scan stores results in the database."""
        mock_derivation.return_value = {
            "/nix/store/test.drv": {}
        }
        mock_vuln.return_value = [
            {
                "pname": "Diff",
                "derivation": "/nix/store/Diff.drv",
                "cvssv3_basescore": {"CVE-2024-13278": 9.1},
            }
        ]
        mock_why.return_value = []
        mock_merge.return_value = {}
        mock_normalize.return_value = [
            {
                "package_name": "Diff",
                "drv_path": "/nix/store/Diff.drv",
                "severity": "CRITICAL",
            }
        ]

        app.run_scan("/run/current-system")

        # Verify scan was stored
        conn = app.get_connection()
        scans = database.get_vulnerabilities_since(conn, "2000-01-01")
        conn.close()
        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0]["package_name"], "Diff")


class TestStoreTreeNodes(unittest.TestCase):
    """Tests for the _store_tree_nodes helper."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        app.DB_PATH = self.db_path
        self.conn = app.get_connection()
        self.scan_id = database.insert_scan(self.conn, "/run/current-system")

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_stores_root_node(self):
        """Root node is stored."""
        tree = {
            "pname": "root-pkg",
            "drv_path": "/nix/store/root.drv",
            "children": [],
        }
        app._store_tree_nodes(self.conn, self.scan_id, tree, 1)
        tree_nodes = database.get_dependency_tree_for_scan(self.conn, self.scan_id)
        self.assertEqual(len(tree_nodes), 1)
        self.assertEqual(tree_nodes[0]["package_name"], "root-pkg")

    def test_stores_nested_nodes(self):
        """Nested nodes are stored."""
        tree = {
            "pname": "root-pkg",
            "drv_path": "/nix/store/root.drv",
            "children": [
                {
                    "pname": "child-pkg",
                    "drv_path": "/nix/store/child.drv",
                    "children": [],
                }
            ],
        }
        app._store_tree_nodes(self.conn, self.scan_id, tree, 1)
        tree_nodes = database.get_dependency_tree_for_scan(self.conn, self.scan_id)
        self.assertEqual(len(tree_nodes), 2)
        pnames = {n["package_name"] for n in tree_nodes}
        self.assertIn("root-pkg", pnames)
        self.assertIn("child-pkg", pnames)

    def test_skips_empty_node(self):
        """Empty nodes are not stored."""
        tree = {"pname": "", "drv_path": "", "children": []}
        app._store_tree_nodes(self.conn, self.scan_id, tree, 1)
        tree_nodes = database.get_dependency_tree_for_scan(self.conn, self.scan_id)
        self.assertEqual(len(tree_nodes), 0)


class TestHealthEndpoint(unittest.TestCase):
    """Tests for the health endpoint via WSGI."""

    def test_health_returns_ok(self):
        """Health endpoint returns status ok."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/health",
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(),
            "wsgi.errors": None,
        }
        start_response = unittest.mock.Mock()
        result = app.app.wsgi(environ, start_response)
        body = b"".join(result)
        status = start_response.call_args[0][0]
        self.assertEqual(status, "200 OK")
        parsed = json.loads(body.decode())
        self.assertEqual(parsed["status"], "ok")


if __name__ == "__main__":
    unittest.main()
