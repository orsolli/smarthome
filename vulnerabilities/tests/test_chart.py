"""Tests for app/chart.py."""

import re
import unittest
from datetime import datetime, timedelta

from app.chart import (
    timeseries_bar_html,
    timeseries_chart_html,
    mini_bar_html,
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
        """Same package with multiple severities shows persisted-state segments."""
        data = [
            {"package_name": "vim", "timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "HIGH"},
            {"package_name": "vim", "timestamp": "2024-09-15T10:00:00", "severity": "CRITICAL"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("vim", html)
        # 3 events produce 4 segments: NONE -> LOW -> HIGH -> CRITICAL
        self.assertEqual(html.count("chart-bar-segment"), 4)

    def test_leading_clean_segment(self):
        """Before the first scan the package is shown as NONE (gray)."""
        data = [
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "HIGH"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("rgba(48, 54, 61, 1.0)", html)
        self.assertIn("NONE from 2024-01-01", html)

    def test_segment_widths_sum_to_100(self):
        """Persisted-state segments cover the whole window exactly."""
        data = [
            {"package_name": "vim", "timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
            {"package_name": "vim", "timestamp": "2024-09-15T10:00:00", "severity": "HIGH"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        widths = [float(w) for w in re.findall(r'width:([\d.]+)%', html)]
        self.assertAlmostEqual(sum(widths), 100.0, places=1)

    def test_last_state_persists_until_end(self):
        """The last recorded severity extends to the end of the window."""
        data = [
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "CRITICAL"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("CRITICAL from 2024-06-15T10:00:00 to 2024-12-31", html)

    def test_intensity_by_severity(self):
        """Segment opacity is fixed per severity level."""
        data = [
            {"package_name": "vim", "timestamp": "2024-06-15T10:00:00", "severity": "LOW"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        self.assertIn("rgba(63, 185, 80, 0.4)", html)  # LOW is a lighter green

    def test_same_timestamp_scans_no_zero_width(self):
        """Two scans at the same timestamp do not create zero-width segments."""
        data = [
            {"package_name": "vim", "timestamp": "2024-01-15T10:00:00", "severity": "LOW"},
            {"package_name": "vim", "timestamp": "2024-01-15T10:00:00", "severity": "HIGH"},
        ]
        html = timeseries_chart_html(data, "2024-01-01", "2024-12-31")
        # NONE (Jan 1 -> Jan 15) then HIGH (Jan 15 -> Dec 31); LOW never persists
        self.assertEqual(html.count("chart-bar-segment"), 2)
        self.assertNotIn("width:0.00%", html)


class TestMiniBarHtml(unittest.TestCase):
    """Tests for the label-free tree bars."""

    def test_empty_timeline_is_clean(self):
        """A node with no events renders one gray track."""
        html = mini_bar_html([], datetime(2024, 1, 1), datetime(2024, 12, 31))
        self.assertIn("chart-bar-track", html)
        self.assertIn("background:#30363d", html)
        self.assertNotIn("chart-bar-label", html)

    def test_segments_cover_the_shared_window(self):
        """Bars use the global window so nodes are comparable."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        html = mini_bar_html(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "CRITICAL"}], start, end
        )
        widths = [float(w) for w in re.findall(r"width:([\d.]+)%", html)]
        self.assertAlmostEqual(sum(widths), 100.0, places=1)
        self.assertIn("rgba(218, 54, 51, 1.0)", html)

    def test_no_label(self):
        """Tree bars never render a package label."""
        html = mini_bar_html(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "HIGH"}],
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
        )
        self.assertNotIn("chart-bar-label", html)


if __name__ == "__main__":
    unittest.main()
