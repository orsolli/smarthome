"""Tests for app/chart.py."""

import re
import unittest
from datetime import datetime

from app.chart import _build_segments, _parse_timestamp, mini_bar_html

START = datetime(2024, 1, 1)
END = datetime(2024, 12, 31)


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


class TestBuildSegments(unittest.TestCase):
    """A segment is the stretch between two scans, coloured by what was in force."""

    def test_no_events_is_one_clean_span(self):
        segments = _build_segments([], START, END)
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0][0], "NONE")

    def test_a_severity_persists_until_the_next_scan(self):
        """One scan recording HIGH splits the window into NONE then HIGH."""
        segments = _build_segments(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "HIGH"}], START, END
        )
        self.assertEqual([sev for sev, *_ in segments], ["NONE", "HIGH"])
        self.assertEqual(segments[0][2], START)
        self.assertEqual(segments[-1][3], END)

    def test_three_scans_make_four_segments(self):
        timeline = [
            {"timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
            {"timestamp": "2024-06-15T10:00:00", "severity": "HIGH"},
            {"timestamp": "2024-09-15T10:00:00", "severity": "CRITICAL"},
        ]
        segments = _build_segments(timeline, START, END)
        self.assertEqual([sev for sev, *_ in segments], ["NONE", "LOW", "HIGH", "CRITICAL"])

    def test_widths_cover_the_window_exactly(self):
        timeline = [
            {"timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
            {"timestamp": "2024-09-15T10:00:00", "severity": "HIGH"},
        ]
        total = sum(width for _, width, *_ in _build_segments(timeline, START, END))
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_two_scans_at_one_time_leave_no_zero_width_gap(self):
        """LOW is overwritten by HIGH at the same instant, so it never persists."""
        timeline = [
            {"timestamp": "2024-01-15T10:00:00", "severity": "LOW"},
            {"timestamp": "2024-01-15T10:00:00", "severity": "HIGH"},
        ]
        segments = _build_segments(timeline, START, END)
        self.assertEqual([sev for sev, *_ in segments], ["NONE", "HIGH"])
        self.assertTrue(all(width > 0 for _, width, *_ in segments))

    def test_events_outside_the_window_are_clamped(self):
        """A scan before the zoomed window still ends the segment it started."""
        timeline = [
            {"timestamp": "2023-01-01T00:00:00", "severity": "CRITICAL"},
            {"timestamp": "2024-06-15T10:00:00", "severity": "NONE"},
        ]
        segments = _build_segments(timeline, START, END)
        self.assertEqual([sev for sev, *_ in segments], ["CRITICAL", "NONE"])
        self.assertEqual(segments[0][2], START)

    def test_the_version_travels_with_the_event(self):
        timeline = [
            {"timestamp": "2024-06-15T10:00:00", "severity": "HIGH", "version": "2.54.1"},
        ]
        segments = _build_segments(timeline, START, END)
        self.assertEqual(segments[0][4], "")
        self.assertEqual(segments[1][4], "2.54.1")

    def test_unsorted_input_is_sorted(self):
        timeline = [
            {"timestamp": "2024-09-15T10:00:00", "severity": "HIGH"},
            {"timestamp": "2024-03-15T10:00:00", "severity": "LOW"},
        ]
        segments = _build_segments(timeline, START, END)
        self.assertEqual([sev for sev, *_ in segments], ["NONE", "LOW", "HIGH"])


class TestMiniBarHtml(unittest.TestCase):
    """Tests for the label-free tree bars."""

    def test_empty_timeline_is_clean(self):
        """A node with no events renders one gray track."""
        html = mini_bar_html([], START, END)
        self.assertIn("chart-bar-track", html)
        self.assertIn("background:#30363d", html)
        self.assertNotIn("chart-bar-label", html)

    def test_segments_cover_the_shared_window(self):
        """Bars use the global window so nodes are comparable."""
        html = mini_bar_html(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "CRITICAL"}], START, END
        )
        widths = [float(w) for w in re.findall(r"width:([\d.]+)%", html)]
        self.assertAlmostEqual(sum(widths), 100.0, places=1)
        self.assertIn("rgba(218, 54, 51, 1.0)", html)

    def test_opacity_is_fixed_per_severity(self):
        html = mini_bar_html(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "LOW"}], START, END
        )
        self.assertIn("rgba(63, 185, 80, 0.4)", html)

    def test_no_label(self):
        """Tree bars never render a package label."""
        html = mini_bar_html(
            [{"timestamp": "2024-06-15T10:00:00", "severity": "HIGH"}], START, END
        )
        self.assertNotIn("chart-bar-label", html)

    def test_the_version_shows_up_in_the_tooltip(self):
        html = mini_bar_html(
            [
                {
                    "timestamp": "2024-06-15T10:00:00",
                    "severity": "HIGH",
                    "version": "2.54.2+abi=4.1",
                }
            ],
            START,
            END,
        )
        self.assertIn("HIGH from 2024-06-15T10:00:00 to 2024-12-31T00:00:00 (2.54.2+abi=4.1)", html)


if __name__ == "__main__":
    unittest.main()
