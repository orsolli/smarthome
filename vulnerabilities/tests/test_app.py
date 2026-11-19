"""Tests for app module core logic."""

import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import BytesIO, StringIO
from unittest.mock import call, patch


def _node_id_for(drv_path: str) -> str:
    """Mirror of app.templates.node_dom_id for asserting DOM ids."""
    return "node-" + re.sub(r"[^A-Za-z0-9_-]", "_", drv_path)


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

    def test_show_more_url_carries_the_window_and_the_offset(self):
        """The lazily loaded children must be zoomed like the bars already drawn."""
        status, body = self._get(f"/api/tree/{self.scan_id}", query="days=30")
        self.assertEqual(status, "200 OK")
        self.assertIn(
            f'hx-get="/api/children/{self.scan_id}{self.root_drv}?days=30&offset=50"',
            body,
        )

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


class TestCliEntryPoint(unittest.TestCase):
    """`python -m app` dispatches scan / serve / merge."""

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.environ["DATABASE_PATH"] = self.db_path
        from app import __main__ as cli_module
        self.cli_module = cli_module

    def tearDown(self):
        os.unlink(self.db_path)

    def test_scan_subcommand_forwards_the_target(self):
        with patch.object(self.cli_module, "cli_main", return_value=0) as mock:
            self.assertEqual(self.cli_module.cli(["scan", "--target", "./result"]), 0)
            mock.assert_called_once_with(["--target", "./result"])

    def test_scan_subcommand_forwards_the_alias_and_date(self):
        """A generation scan is recorded under the system it belongs to."""
        with patch.object(self.cli_module, "cli_main", return_value=0) as mock:
            self.assertEqual(
                self.cli_module.cli(
                    [
                        "scan",
                        "--target", "/nix/var/nix/profiles/system-2-link",
                        "--as-target", "/run/current-system",
                        "--at", "2025-10-14T08:21:00",
                    ]
                ),
                0,
            )
            mock.assert_called_once_with(
                [
                    "--target", "/nix/var/nix/profiles/system-2-link",
                    "--as-target", "/run/current-system",
                    "--at", "2025-10-14T08:21:00",
                ]
            )

    def test_serve_subcommand_sets_the_bind_address(self):
        original = os.environ.get("BIND_ADDRESS")
        with patch.object(self.cli_module, "main", return_value=None):
            self.assertEqual(
                self.cli_module.cli(["serve", "--bind", "127.0.0.1:8092"]), 0
            )
        self.assertEqual(os.environ["BIND_ADDRESS"], "127.0.0.1:8092")
        if original is None:
            del os.environ["BIND_ADDRESS"]
        else:
            os.environ["BIND_ADDRESS"] = original

    def test_merge_subcommand_reads_trees_from_stdin(self):
        text = (
            "/nix/store/sysdrv000000000000000000000000000000-nixos-system.drv\n"
            "└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv\n"
            "    └───/nix/store/xdgdrv000000000000000000000000000000-xdg-utils-9.99.0.drv\n"
            "/nix/store/sysdrv000000000000000000000000000000-nixos-system.drv\n"
            "└───/nix/store/etcdrv000000000000000000000000000000-etc.drv\n"
        )
        buffer = StringIO(text)
        out = StringIO()
        with patch("sys.stdin", buffer), redirect_stdout(out):
            self.assertEqual(self.cli_module.cli(["merge", "--format", "ascii"]), 0)
        self.assertIn("system-path", out.getvalue())
        self.assertIn("etc", out.getvalue())

    def test_no_subcommand_is_an_error(self):
        with self.assertRaises(SystemExit) as raised:
            self.cli_module.cli([])
        self.assertEqual(raised.exception.code, 2)

    def test_cli_main_returns_exit_codes(self):
        import app.app as app_module
        with patch.object(app_module, "run_scan", return_value={"error": "boom"}):
            with redirect_stdout(StringIO()):
                self.assertEqual(app_module.cli_main(["--target", "./result"]), 1)
        with patch.object(
            app_module,
            "run_scan",
            return_value={"scan_id": 1, "target": "./result", "vulnerabilities_found": 0},
        ):
            with redirect_stdout(StringIO()):
                self.assertEqual(app_module.cli_main(["--target", "./result"]), 0)

    def test_cli_main_reports_the_generation_it_backfilled(self):
        import app.app as app_module
        out = StringIO()
        with patch.object(
            app_module,
            "run_scan",
            return_value={
                "scan_id": 5,
                "target": "/run/current-system",
                "scanned_path": "/nix/var/nix/profiles/system-2-link",
                "timestamp": "2025-10-14T08:21:00",
                "vulnerabilities_found": 0,
            },
        ) as run_scan:
            with redirect_stdout(out):
                self.assertEqual(
                    app_module.cli_main(
                        [
                            "--target", "/nix/var/nix/profiles/system-2-link",
                            "--as-target", "/run/current-system",
                            "--at", "2025-10-14T08:21:00",
                        ]
                    ),
                    0,
                )
        self.assertEqual(
            run_scan.call_args,
            call(
                "/nix/var/nix/profiles/system-2-link",
                label="/run/current-system",
                timestamp="2025-10-14T08:21:00",
            ),
        )
        self.assertIn("Scanned path: /nix/var/nix/profiles/system-2-link", out.getvalue())
        self.assertIn("Recorded at: 2025-10-14T08:21:00", out.getvalue())


class TestTargetListAndZoom(unittest.TestCase):
    """The home page lists targets; ?days= zooms a scan's timeline window."""

    HASH = "abcdefghijklmnopqrstuvwxyz01234567"

    def setUp(self):
        import core.database as database
        from core.scanner import ScanPipeline

        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.environ["DATABASE_PATH"] = self.db_path
        self.conn = database.init_db(self.db_path)

        self.system = [
            database.insert_scan(
                self.conn, "/run/current-system",
                timestamp="2024-10-01T00:00:00",
                scanned_path="/nix/var/nix/profiles/system-2-link",
            ),
            database.insert_scan(
                self.conn, "/run/current-system",
                timestamp="2024-11-01T00:00:00",
                scanned_path="/nix/var/nix/profiles/system-3-link",
            ),
            database.insert_scan(
                self.conn, "/run/current-system",
                timestamp="2024-11-15T00:00:00",
                scanned_path="/nix/var/nix/profiles/system-5-link",
            ),
        ]
        self.other = database.insert_scan(
            self.conn, "./result", timestamp="2024-11-20T00:00:00"
        )

        for scan_id in self.system + [self.other]:
            root = database.insert_dependency_node(
                self.conn, scan_id, "system", f"/nix/store/{self.HASH}-system.drv"
            )
            database.insert_dependency_node(
                self.conn, scan_id, "perl", f"/nix/store/{self.HASH}-perl-5.34.drv",
                parent_id=root,
            )
            database.insert_vulnerability_event(
                self.conn, scan_id, "perl", f"/nix/store/{self.HASH}-perl-5.34.drv",
                "CRITICAL",
            )
        self.conn.commit()

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
        from unittest.mock import Mock
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "wsgi.input": BytesIO(),
            "wsgi.errors": None,
        }
        start_response = Mock()
        body = b"".join(self.app_module.app.wsgi(environ, start_response))
        return start_response.call_args[0][0], body.decode()

    def test_home_page_lists_each_target_once(self):
        status, body = self._get("/")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body.count('class="target-item"'), 2)
        self.assertIn("/run/current-system", body)
        self.assertIn("./result", body)

    def test_target_row_shows_scan_count_and_latest_date(self):
        status, body = self._get("/")
        self.assertIn("3 scans", body)
        self.assertIn("1 scan · 2024-11-20", body)

    def test_home_page_links_to_the_latest_scan_of_a_target(self):
        status, body = self._get("/")
        self.assertIn(f'href="/scan/{self.system[-1]}"', body)
        self.assertIn(f'href="/scan/{self.other}"', body)

    def test_scan_page_names_the_generation_it_scanned(self):
        status, body = self._get(f"/scan/{self.system[0]}")
        self.assertEqual(status, "200 OK")
        self.assertIn("/nix/var/nix/profiles/system-2-link", body)
        self.assertIn("2024-10-01 00:00", body)

    def test_scan_page_offers_window_chips(self):
        status, body = self._get(f"/scan/{self.system[-1]}")
        self.assertEqual(body.count('class="chip'), 4)
        self.assertIn('class="chip active" href="/scan/', body)  # "all" is active

    def test_the_active_chip_matches_the_current_window(self):
        status, body = self._get(f"/scan/{self.system[-1]}", query="days=7")
        self.assertIn(f'class="chip active" href="/scan/{self.system[-1]}?days=7"', body)
        self.assertIn(f'class="chip" href="/scan/{self.system[-1]}?days=30"', body)

    def test_lazy_bar_urls_keep_the_window(self):
        status, body = self._get(f"/api/tree/{self.system[-1]}", query="days=7")
        self.assertEqual(status, "200 OK")
        self.assertIn(f'hx-get="/api/bars/{self.system[-1]}?days=7"', body)

    def test_zooming_drops_the_older_bar_boundaries(self):
        _, full = self._get(f"/api/bars/{self.system[-1]}")
        _, zoomed = self._get(f"/api/bars/{self.system[-1]}", query="days=7")
        # Two bars, each split by the three scans: 4 segments over the full
        # history, 2 in a window that only contains the last scan.
        self.assertEqual(full.count("chart-bar-segment"), 8)
        self.assertEqual(zoomed.count("chart-bar-segment"), 4)
        self.assertIn("2024-10-01T00:00:00", full)
        self.assertNotIn("2024-10-01T00:00:00", zoomed)


class TestNodeIdsAreCssSafe(unittest.TestCase):
    """HTMX finds an out-of-band bar swap with `#<id>`, so a node id that
    carries `+` or `=` never matches and the node keeps an empty timeline."""

    def test_characters_outside_a_css_identifier_are_flattened(self):
        from app.templates import node_dom_id

        self.assertEqual(
            node_dom_id("/nix/store/abc-webkitgtk-9.99.0+abi=1.0.drv"),
            "node-_nix_store_abc-webkitgtk-9_99_0_abi_1_0_drv",
        )
        self.assertEqual(
            node_dom_id("/nix/store/abc-xvfb-run-1+g87f6705.drv"),
            "node-_nix_store_abc-xvfb-run-1_g87f6705_drv",
        )

    def test_the_tree_slot_and_the_bar_share_one_css_safe_id(self):
        import core.database as database
        from core.scanner import ScanPipeline

        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        try:
            conn = database.init_db(db_path)
            scan_id = database.insert_scan(conn, "/run/current-system")
            root = database.insert_dependency_node(
                conn, scan_id, "system", "/nix/store/abc-system.drv"
            )
            drv = "/nix/store/abc-webkitgtk-9.99.0+abi=1.0.drv"
            database.insert_dependency_node(
                conn, scan_id, "webkitgtk", drv, parent_id=root
            )
            database.insert_vulnerability_event(conn, scan_id, "webkitgtk", drv, "HIGH")
            conn.commit()
            conn.close()

            os.environ["DATABASE_PATH"] = db_path
            import app.app as app_module
            app_module.DB_PATH = db_path
            app_module.pipeline = ScanPipeline.default()
            app_module.pipeline.storage = app_module.DatabaseStorage(db_path)

            from unittest.mock import Mock
            environ = {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": f"/api/tree/{scan_id}",
                "QUERY_STRING": "",
                "wsgi.input": BytesIO(),
                "wsgi.errors": None,
            }
            start_response = Mock()
            tree = b"".join(app_module.app.wsgi(environ, start_response)).decode()

            environ["PATH_INFO"] = f"/api/bars/{scan_id}/nix/store/abc-system.drv"
            start_response = Mock()
            bars = b"".join(app_module.app.wsgi(environ, start_response)).decode()

            slot = 'id="node-_nix_store_abc-webkitgtk-9_99_0_abi_1_0_drv-timeline"'
            self.assertIn(slot, tree)
            self.assertIn(slot, bars)
            self.assertIn("chart-bar-segment", bars)
            ids = re.findall(r'id="(node-[^"]*)"', tree)
            self.assertTrue(ids, "no node ids in the tree")
            for node_id in ids:
                self.assertIsNotNone(
                    re.fullmatch(r"[A-Za-z0-9_-]+", node_id),
                    f"id {node_id!r} is not a bare CSS identifier",
                )
        finally:
            try:
                os.close(db_fd)
            except Exception:
                pass
            os.unlink(db_path)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
