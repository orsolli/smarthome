"""Tests for core/severity.py, the single definition of severity levels."""

import unittest

from core.severity import (
    SEVERITY_INTENSITY,
    SEVERITY_LABELS,
    SEVERITY_RANK,
    SEVERITY_RGB,
    aggregate_severity,
    severity_bg_color,
    severity_color,
    severity_from_cvss,
    severity_label,
    severity_rank,
    severity_rgba,
)


class TestSeverityLevels(unittest.TestCase):
    """Every level has a rank, a color, an intensity and a label."""

    def test_levels_are_ordered(self):
        self.assertEqual(
            [sev for sev, _ in sorted(SEVERITY_RANK.items(), key=lambda x: x[1])],
            ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
        )

    def test_every_level_is_complete(self):
        for severity in SEVERITY_RANK:
            self.assertIn(severity, SEVERITY_RGB)
            self.assertIn(severity, SEVERITY_INTENSITY)
            self.assertIn(severity, SEVERITY_LABELS)

    def test_unknown_severity_ranks_as_none(self):
        self.assertEqual(severity_rank("BOGUS"), 0)
        self.assertEqual(severity_rank("NONE"), 0)


class TestSeverityFromCvss(unittest.TestCase):
    """CVSS bands map to the shared labels."""

    def test_critical(self):
        self.assertEqual(severity_from_cvss(9.8), "CRITICAL")

    def test_high(self):
        self.assertEqual(severity_from_cvss(7.0), "HIGH")

    def test_medium(self):
        self.assertEqual(severity_from_cvss(4.0), "MEDIUM")

    def test_low(self):
        self.assertEqual(severity_from_cvss(3.9), "LOW")


class TestAggregateSeverity(unittest.TestCase):
    """A parent is as red as its worst child."""

    def test_empty(self):
        self.assertEqual(aggregate_severity([]), "NONE")

    def test_all_clean(self):
        self.assertEqual(aggregate_severity(["NONE", "NONE"]), "NONE")

    def test_worst_wins(self):
        self.assertEqual(aggregate_severity(["LOW", "HIGH", "MEDIUM"]), "HIGH")
        self.assertEqual(
            aggregate_severity(["CRITICAL", "HIGH", "MEDIUM", "LOW"]), "CRITICAL"
        )

    def test_unknown_values_are_ignored(self):
        self.assertEqual(aggregate_severity(["NONE", "BOGUS"]), "NONE")


class TestSeverityColors(unittest.TestCase):
    """Colors come from the one RGB table."""

    def test_hex_colors(self):
        self.assertEqual(severity_color("CRITICAL"), "#da3633")
        self.assertEqual(severity_color("NONE"), "#30363d")
        self.assertEqual(severity_color("BOGUS"), "#30363d")

    def test_background_tint(self):
        self.assertEqual(severity_bg_color("CRITICAL"), "rgba(218, 54, 51, 0.3)")
        self.assertEqual(severity_bg_color("NONE"), "rgba(48, 54, 61, 0.1)")

    def test_segment_opacity(self):
        self.assertEqual(severity_rgba("HIGH", 0.8), "rgba(240, 136, 62, 0.8)")
        self.assertEqual(severity_rgba("HIGH", 2.0), "rgba(240, 136, 62, 1.0)")
        self.assertEqual(severity_rgba("HIGH", -1.0), "rgba(240, 136, 62, 0.0)")

    def test_labels(self):
        self.assertEqual(severity_label("NONE"), "Clean")
        self.assertEqual(severity_label("BOGUS"), "Unknown")


if __name__ == "__main__":
    unittest.main()
