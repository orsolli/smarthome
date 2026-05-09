"""Tests for app/chart.py."""

import unittest
from datetime import datetime, timedelta

from app.chart import (
    timeseries_bar_html,
    timeseries_chart_html,
    _severity_to_color,
    _parse_timestamp,
)


class TestSeverityToColor(unittest.TestCase):
    """Tests for _severity_to_color."""

    def test_critical_color(self):
        color = _severity_to_color("CRITICAL")
        self.assertIn("rgba(218, 54, 51", color)

    def test_high_color(self):
        color = _severity_to_color("HIGH")
        self.assertIn("rgba(240, 136, 62", color)

    def test_medium_color(self):
        color = _severity_to_color("MEDIUM")
        self.assertIn("rgba(210, 153, 34", color)

    def test_low_color(self):
        color = _severity_to_color("LOW")
        self.assertIn("rgba(63, 185, 80", color)

    def test_none_color(self):
        color = _severity_to_color("NONE")
        self.assertIn("rgba(48, 54, 61", color)

    def test_intensity_reduces_alpha(self):
        full = _severity_to_color("CRITICAL", 1.0)
        dim = _severity_to_color("CRITICAL", 0.5)
        self.assertIn(", 1.0)", full)
        self.assertIn(", 0.5)", dim)


class TestParseTimestamp(unittest.TestCase):
    """Tests for _parse_timestamp."""

    def test_valid_iso(self):
        result = _parse_timestamp("2024-01-15T10:30:00")
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_invalid_returns_min(self):
        result = _parse_timestamp("not-a-date")
        self.assertEqual(result, datetime.min)

    def test_none_returns_min(self):
        result = _parse_timestamp("")
        self.assertEqual(result, datetime.min)


class TestTimeseriesBarHtml(unittest.TestCase):
    """Tests for timeseries_bar_html."""

    def test_empty_timeline(self):
        """Empty timeline shows gray bar."""
        html = timeseries_bar_html(
            "test-pkg",
            [],
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )
        self.assertIn("test-pkg", html)
        self.assertIn("#30363d", html)

    def test_with_severity(self):
        """Timeline with events shows colored segments."""
        timeline = [
            {"timestamp": "2024-06-15T10:00:00", "severity": "CRITICAL"},
            {"timestamp": "2024-09-15T10:00:00", "severity": "HIGH"},
        ]
        html = timeseries_bar_html(
            "test-pkg",
            timeline,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )
        self.assertIn("test-pkg", html)
        self.assertIn("chart-bar-track", html)
        self.assertIn("chart-bar-segment", html)
        # CRITICAL should have red color
        self.assertIn("rgba(218, 54, 51", html)


class TestTimeseriesChartHtml(unittest.TestCase):
    """Tests for timeseries_chart_html."""

    def test_empty_data(self):
        """Empty data produces chart with no bars."""
        html = timeseries_chart_html([], "2024-01-01", "2024-12-31")
        self.assertIn("Vulnerability Timeline", html)
        self.assertIn("timeline-chart", html)

    def test_single_package(self):
        """Single package produces one bar."""
        data = [
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "HIGH"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("vim", html)
        self.assertIn("chart-bar", html)

    def test_multiple_packages_sorted(self):
        """Multiple packages are sorted alphabetically."""
        data = [
            {"package_name": "zsh", "timestamp": "2024-06-15T10:00:00", "severity": "LOW"},
            {"package_name": "bash", "timestamp": "2024-06-15T10:00:00", "severity": "MEDIUM"},
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "CRITICAL"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        # bash should come before vim in the HTML
        bash_pos = html.find("bash")
        vim_pos = html.find("vim")
        self.assertLess(bash_pos, vim_pos)

    def test_multiple_severities_for_same_package(self):
        """Same package with multiple severities shows multiple segments."""
        data = [
            {"package_name": "vim", "timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "HIGH"},
            {"package_name": "vim", "timestamp": "2024-09-15T10:00:00", "severity": "CRITICAL"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("vim", html)
        # Should have 3 segments for 3 events
        self.assertEqual(html.count("chart-bar-segment"), 3)


if __name__ == "__main__":
    unittest.main()
