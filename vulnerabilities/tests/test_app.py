"""Tests for app module core logic."""

import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch


class TestRunScan(unittest.TestCase):
    """Tests for the run_scan function using the new ScanPipeline."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        os.environ["DATABASE_PATH"] = self.db_path
        from app import app
        app.DB_PATH = self.db_path
        # Replace pipeline storage with real database storage
        app.pipeline.storage = app.DatabaseStorage(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_scan_returns_results(self):
        from app import app
        """run_scan returns correct vulnerability results."""
        result = app.run_scan("/run/current-system")

        self.assertEqual(result["vulnerabilities_found"], 2)
        self.assertEqual(result["target"], "/run/current-system")
        pnames = {v["package_name"] for v in result["vulnerabilities"]}
        self.assertIn("Diff", pnames)
        self.assertIn("ShellCheck", pnames)

    def test_scan_no_derivation_returns_error(self):
        from app import app
        """run_scan returns error when no derivation found."""
        # Patch the pipeline's derivation source to return empty
        with patch.object(app.pipeline.derivation_source, 'show_derivation', return_value={}):
            result = app.run_scan("/nonexistent")
        self.assertIn("error", result)

    def test_scan_stores_in_database(self):
        from app import app
        """run_scan stores results in the database."""
        import core.database as database
        app.run_scan("/run/current-system")

        # Verify scan was stored
        conn = database.init_db(self.db_path)
        events = database.get_vulnerabilities_since(conn, "2000-01-01")
        conn.close()
        self.assertGreater(len(events), 0)
        pnames = {e["package_name"] for e in events}
        self.assertIn("Diff", pnames)


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
        import app.app as app
        result = app.app.wsgi(environ, start_response)
        body = b"".join(result)
        status = start_response.call_args[0][0]
        self.assertEqual(status, "200 OK")
        parsed = json.loads(body.decode())
        self.assertEqual(parsed["status"], "ok")


class TestJsonListEndpoints(unittest.TestCase):
    """List-returning endpoints must serialize to JSON (Bottle 0.13
    only auto-serializes dict returns, not lists)."""

    def setUp(self):
        self.db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.db_file.name
        self.db_file.close()
        os.environ["DATABASE_PATH"] = self.db_path
        import app.app as app_module
        self.app_module = app_module
        app_module.DB_PATH = self.db_path
        app_module.pipeline.storage = app_module.DatabaseStorage(self.db_path)
        result = app_module.run_scan("/run/current-system")
        self.scan_id = result["scan_id"]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def _get(self, path):
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "QUERY_STRING": "",
            "wsgi.input": BytesIO(),
            "wsgi.errors": None,
        }
        start_response = unittest.mock.Mock()
        body = b"".join(self.app_module.app.wsgi(environ, start_response))
        status = start_response.call_args[0][0]
        headers = dict(start_response.call_args[0][1])
        return status, body, headers

    def test_vulnerabilities_returns_json_list(self):
        status, body, headers = self._get("/vulnerabilities")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "application/json")
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_tree_returns_json_list(self):
        status, body, headers = self._get(f"/tree/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "application/json")
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_timeseries_returns_json_list(self):
        status, body, headers = self._get("/timeseries")
        self.assertEqual(status, "200 OK")
        self.assertEqual(headers.get("Content-Type"), "application/json")
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
