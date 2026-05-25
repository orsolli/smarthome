"""Tests for dashboard chart rendering with test data.

Tests the full stack: DB → API → HTML template → chart container presence.
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
import unittest.mock
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDashboardCharts(unittest.TestCase):
    """Verify charts render correctly with test data."""

    def setUp(self):
        """Create a temp SQLite DB with test data using SQLite time modifiers.

        Data ranges:
        - / : 10 days of hourly data (days 0-9 ago)
        - /home : 5 days of hourly data (days 0-4 ago)

        High-res query uses 7-day window -> / gets 7*24=168 rows, /home gets 5*24=120 rows
        Daily query uses 365-day window -> / gets 10 rows, /home gets 5 rows
        """
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE disk_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filesystem TEXT NOT NULL,
                total_bytes INTEGER NOT NULL,
                used_bytes INTEGER NOT NULL,
                available_bytes INTEGER NOT NULL,
                mounted_on TEXT NOT NULL
            )
        ''')

        # Insert 10 days of hourly data for /
        for day in range(10):
            for hour in range(24):
                ts = f"datetime('now', '-{day} days', '-{hour} hours')"
                used = 50_000_000_000 + (day * 1_000_000_000) + (hour * 100_000_000)
                total = 100_000_000_000
                available = total - used
                sql = (f"INSERT INTO disk_usage (timestamp, filesystem, total_bytes, "
                       f"used_bytes, available_bytes, mounted_on) VALUES "
                       f"({ts}, '/dev/sda1', {total}, {used}, {available}, '/')")
                cursor.execute(sql)

        # Insert 5 days of hourly data for /home
        for day in range(5):
            for hour in range(24):
                ts = f"datetime('now', '-{day} days', '-{hour} hours')"
                used = 200_000_000_000 + (day * 500_000_000) + (hour * 50_000_000)
                total = 500_000_000_000
                available = total - used
                sql = (f"INSERT INTO disk_usage (timestamp, filesystem, total_bytes, "
                       f"used_bytes, available_bytes, mounted_on) VALUES "
                       f"({ts}, '/dev/sda2', {total}, {used}, {available}, '/home')")
                cursor.execute(sql)

        conn.commit()

        # Verify data was inserted
        cursor.execute('SELECT COUNT(*) FROM disk_usage')
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0, f"Expected rows in test DB, got {count}")

        conn.close()

        os.environ["DATABASE_PATH"] = self.db_path

        # Force re-import of modules with fresh DB
        for mod in list(sys.modules.keys()):
            if mod in ('app.web', 'core.database', 'frontend.home'):
                del sys.modules[mod]

        from app import web
        self.web_app = web.app

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def _make_request(self, path, query_string=""):
        """Make a WSGI request and return status, headers, body."""
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "wsgi.input": BytesIO(),
            "wsgi.errors": None,
        }
        start_response = unittest.mock.Mock()
        result = self.web_app.wsgi(environ, start_response)
        body = b"".join(result)
        status = start_response.call_args[0][0]
        return status, start_response.call_args[0][1], body

    # -- Health --

    def test_health_returns_ok(self):
        """Health endpoint returns status ok."""
        status, headers, body = self._make_request("/health")
        self.assertEqual(status, "200 OK")
        self.assertEqual(json.loads(body.decode())["status"], "ok")

    # -- Home page (HTML template) --

    def test_home_returns_htmx_template(self):
        """Home page returns HTML with HTMX + Plotly + chart containers."""
        status, headers, body = self._make_request("/")
        self.assertEqual(status, "200 OK")
        html = body.decode()
        self.assertIn('Plotly', html)
        self.assertIn('htmx', html)
        self.assertIn('hx-get="/get_filesystems"', html)
        self.assertIn('chart-container', html)
        # self.assertIn('id="chart-', html) javascript is not enabled by this test

    # -- Filesystem cards --

    def test_get_filesystems_returns_html_cards(self):
        """Filesystem endpoint returns HTML cards with data attributes."""
        status, headers, body = self._make_request("/get_filesystems")
        self.assertEqual(status, "200 OK")
        html = body.decode()
        self.assertIn('data-mounted-on="/"', html)
        self.assertIn('data-mounted-on="/home"', html)
        self.assertIn('1Y', html)
        self.assertIn('1W', html)
        self.assertIn('fs-card', html)

    # -- High-res data (7-day window) --

    def test_get_usage_history_high_res(self):
        """High-res endpoint returns raw measurements as JSON.

        / has 10 days of data, but high-res query uses 7-day window -> 7*24=168 rows
        """
        status, headers, body = self._make_request("/get_usage_history/", "range=1w")
        self.assertEqual(status, "200 OK")
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "High-res should return data points")
        self.assertIn("timestamp", data[0])
        self.assertIn("used_bytes", data[0])
        self.assertIn("available_bytes", data[0])
        self.assertIn("total_bytes", data[0])
        # 7 days * 24 hours = 168 entries for / (within 7-day window)
        self.assertEqual(len(data), 168)

    # -- Daily (candlestick) data (365-day window) --

    def test_get_usage_history_daily(self):
        """Daily endpoint returns aggregated candlestick data (1 per day).

        / has 10 days of data, daily query uses 365-day window -> 10 rows + overlap
        """
        status, headers, body = self._make_request("/get_usage_history/", "range=1y")
        self.assertEqual(status, "200 OK")
        data = json.loads(body.decode())
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0, "Daily should return data points")
        self.assertIn("timestamp", data[0])
        self.assertIn("open_bytes", data[0])
        self.assertIn("high_bytes", data[0])
        self.assertIn("low_bytes", data[0])
        self.assertIn("close_bytes", data[0])
        self.assertIn("total_bytes", data[0])
        # 10 days = 10+overlap candles for /
        self.assertAlmostEqual(len(data), 10, delta=1)

    # -- Data consistency --

    def test_chart_data_consistency(self):
        """High-res and daily data should agree on total_bytes."""
        _, _, high_body = self._make_request("/get_usage_history/", "range=1w")
        _, _, daily_body = self._make_request("/get_usage_history/", "range=1y")

        high_data = json.loads(high_body.decode())
        daily_data = json.loads(daily_body.decode())

        self.assertEqual(high_data[0]["total_bytes"], daily_data[0]["total_bytes"])

    def test_daily_candlestick_logic(self):
        """Verify candlestick values make sense (open/close within high/low)."""
        _, _, daily_body = self._make_request("/get_usage_history/", "range=1y")
        data = json.loads(daily_body.decode())

        for candle in data:
            self.assertGreaterEqual(candle["high_bytes"], candle["open_bytes"])
            self.assertGreaterEqual(candle["high_bytes"], candle["close_bytes"])
            self.assertLessEqual(candle["low_bytes"], candle["open_bytes"])
            self.assertLessEqual(candle["low_bytes"], candle["close_bytes"])

    def test_high_res_has_more_data_points(self):
        """High-res should return significantly more points than daily."""
        _, _, high_body = self._make_request("/get_usage_history/", "range=1w")
        _, _, daily_body = self._make_request("/get_usage_history/", "range=1y")

        high_count = len(json.loads(high_body.decode()))
        daily_count = len(json.loads(daily_body.decode()))
        self.assertGreater(high_count, daily_count * 10)


if __name__ == "__main__":
    unittest.main()
