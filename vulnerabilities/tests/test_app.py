"""Tests for app module core logic."""

import json
import os
import tempfile
import unittest
from io import BytesIO
from unittest.mock import patch


def _node_id_for(drv_path: str) -> str:
    """Mirror of app.api._node_id for asserting DOM ids."""
    return f"node-{drv_path.replace('/', '_').replace('.', '_')}"


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


class TestTreeTimelineWiring(unittest.TestCase):
    """Tests for Phase 3 wiring: timeline slots in the tree and the
    out-of-band bar endpoints that fill them on expansion."""

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
        return status, body.decode()

    def _roots(self):
        import core.database as database
        conn = database.init_db(self.db_path)
        try:
            return [n for n in database.get_dependency_tree_for_scan(conn, self.scan_id)
                    if n["parent_id"] is None]
        finally:
            conn.close()

    def test_tree_html_has_timeline_slots(self):
        status, body = self._get(f"/api/tree/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertIn('class="node-timeline"', body)
        self.assertIn('hx-trigger="node-expanded"', body)
        self.assertIn(f'hx-get="/api/bars/{self.scan_id}/', body)

    def test_scan_page_has_no_standalone_chart(self):
        status, body = self._get(f"/scan/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertIn('id="tree-root"', body)
        self.assertNotIn("Vulnerability Timeline", body)

    def test_tree_response_bootstraps_bars(self):
        """The bootstrap request rides with the tree HTML, so the bars
        swap into nodes that are already in the DOM."""
        status, body = self._get(f"/api/tree/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertIn('id="bars-bootstrap"', body)
        self.assertIn(f'hx-get="/api/bars/{self.scan_id}"', body)
        self.assertIn('hx-trigger="load"', body)

    def test_bootstrap_bars_fill_roots_and_children(self):
        status, body = self._get(f"/api/bars/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        oob_divs = body.count('hx-swap-oob="true"')
        self.assertGreater(oob_divs, 1)
        # The mock scan contains CRITICAL vulns, which bubble up to the root
        self.assertIn("rgba(218, 54, 51", body)
        for root in self._roots():
            self.assertIn(f'{_node_id_for(root["drv_path"])}-timeline', body)

    def test_expansion_bars_fill_children_only(self):
        root = self._roots()[0]
        status, body = self._get(f"/api/bars/{self.scan_id}{root['drv_path']}")
        self.assertEqual(status, "200 OK")
        # No bar for the expanded node itself, only for its children
        self.assertNotIn(f'{_node_id_for(root["drv_path"])}-timeline', body)
        self.assertIn("chart-bar-segment", body)

    def test_bars_for_unknown_path(self):
        status, body = self._get(f"/api/bars/{self.scan_id}/nix/store/nope.drv")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body, "")


class TestChildrenLimit(unittest.TestCase):
    """A node with more than MAX_VISIBLE_CHILDREN children is truncated
    and the remainder is loaded lazily."""

    def setUp(self):
        import core.database as database
        from core.scanner import ScanPipeline

        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.environ["DATABASE_PATH"] = self.db_path
        self.conn = database.init_db(self.db_path)
        self.scan_id = database.insert_scan(self.conn, "./result")
        self.root = database.insert_dependency_node(
            self.conn, self.scan_id, "system", "/nix/store/system.drv"
        )
        for i in range(60):
            severity = "LOW" if i < 50 else "CRITICAL"
            database.insert_dependency_node(
                self.conn, self.scan_id, f"pkg{i}", f"/nix/store/pkg{i}.drv",
                parent_id=self.root,
            )
            database.insert_vulnerability_event(
                self.conn, self.scan_id, f"pkg{i}", f"/nix/store/pkg{i}.drv", severity
            )
        self.conn.commit()
        self.root_drv = "/nix/store/system.drv"

        import app.app as app_module
        app_module.DB_PATH = self.db_path
        app_module.pipeline = ScanPipeline.default()
        app_module.pipeline.storage = app_module.DatabaseStorage(self.db_path)
        self.app_module = app_module

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

    def _get(self, path, query=""):
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "wsgi.input": BytesIO(),
            "wsgi.errors": None,
        }
        start_response = unittest.mock.Mock()
        body = b"".join(self.app_module.app.wsgi(environ, start_response))
        return start_response.call_args[0][0], body.decode()

    def test_tree_truncates_children(self):
        status, body = self._get(f"/api/tree/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body.count("tree-node-header"), 51)  # root + 50 children
        self.assertIn("show 10 more children", body)
        self.assertIn('hx-get="/api/children/', body)

    def test_children_endpoint_returns_the_rest(self):
        status, body = self._get(
            f"/api/children/{self.scan_id}{self.root_drv}", "offset=50"
        )
        self.assertEqual(status, "200 OK")
        self.assertEqual(body.count("tree-node-header"), 10)
        self.assertEqual(body.count('hx-swap-oob="true"'), 10)
        # CRITICAL children sort first, so the hidden tail is the last 10 LOW ones
        self.assertIn("pkg49", body)
        self.assertNotIn("pkg50", body)

    def test_bootstrap_covers_visible_children(self):
        status, body = self._get(f"/api/bars/{self.scan_id}")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body.count('hx-swap-oob="true"'), 51)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
