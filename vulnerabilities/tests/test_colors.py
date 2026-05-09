"""Tests for app/colors.py."""

import unittest

from app.colors import (
    aggregate_severity,
    severity_bg_color,
    severity_color,
    severity_label,
    SEVERITY_COLORS,
    SEVERITY_ORDER,
)


class TestSeverityColors(unittest.TestCase):
    """Tests for severity color constants."""

    def test_all_severities_have_colors(self):
        """All severity levels have defined colors."""
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"):
            self.assertIn(sev, SEVERITY_COLORS)
            self.assertEqual(len(SEVERITY_COLORS[sev]), 2)

    def test_severity_order(self):
        """Severity order is correct."""
        self.assertEqual(SEVERITY_ORDER["CRITICAL"], 4)
        self.assertEqual(SEVERITY_ORDER["HIGH"], 3)
        self.assertEqual(SEVERITY_ORDER["MEDIUM"], 2)
        self.assertEqual(SEVERITY_ORDER["LOW"], 1)
        self.assertEqual(SEVERITY_ORDER["NONE"], 0)


class TestSeverityColor(unittest.TestCase):
    """Tests for severity_color function."""

    def test_critical_color(self):
        """CRITICAL returns red hex."""
        self.assertEqual(severity_color("CRITICAL"), "#da3633")

    def test_high_color(self):
        """HIGH returns orange hex."""
        self.assertEqual(severity_color("HIGH"), "#f0883e")

    def test_medium_color(self):
        """MEDIUM returns yellow hex."""
        self.assertEqual(severity_color("MEDIUM"), "#d29922")

    def test_low_color(self):
        """LOW returns green hex."""
        self.assertEqual(severity_color("LOW"), "#3fb950")

    def test_none_color(self):
        """NONE returns gray hex."""
        self.assertEqual(severity_color("NONE"), "#30363d")

    def test_unknown_returns_none_color(self):
        """Unknown severity falls back to NONE color."""
        self.assertEqual(severity_color("UNKNOWN"), "#30363d")


class TestSeverityBgColor(unittest.TestCase):
    """Tests for severity_bg_color function."""

    def test_critical_bg(self):
        """CRITICAL returns semi-transparent red."""
        self.assertIn("rgba(218, 54, 51, 0.3)", severity_bg_color("CRITICAL"))

    def test_high_bg(self):
        """HIGH returns semi-transparent orange."""
        self.assertIn("rgba(240, 136, 62, 0.25)", severity_bg_color("HIGH"))

    def test_none_bg(self):
        """NONE returns semi-transparent gray."""
        self.assertIn("rgba(48, 54, 61, 0.1)", severity_bg_color("NONE"))


class TestSeverityLabel(unittest.TestCase):
    """Tests for severity_label function."""

    def test_critical_label(self):
        self.assertEqual(severity_label("CRITICAL"), "Critical")

    def test_high_label(self):
        self.assertEqual(severity_label("HIGH"), "High")

    def test_medium_label(self):
        self.assertEqual(severity_label("MEDIUM"), "Medium")

    def test_low_label(self):
        self.assertEqual(severity_label("LOW"), "Low")

    def test_none_label(self):
        self.assertEqual(severity_label("NONE"), "Clean")

    def test_unknown_label(self):
        self.assertEqual(severity_label("UNKNOWN"), "Unknown")


class TestAggregateSeverity(unittest.TestCase):
    """Tests for aggregate_severity function."""

    def test_empty_list(self):
        """Empty list returns NONE."""
        self.assertEqual(aggregate_severity([]), "NONE")

    def test_all_none(self):
        """All NONE returns NONE."""
        self.assertEqual(aggregate_severity(["NONE", "NONE"]), "NONE")

    def test_single_critical(self):
        """Single CRITICAL returns CRITICAL."""
        self.assertEqual(aggregate_severity(["CRITICAL"]), "CRITICAL")

    def test_mixed_returns_highest(self):
        """Mixed severities returns the highest."""
        self.assertEqual(aggregate_severity(["LOW", "HIGH", "MEDIUM"]), "HIGH")

    def test_critical_overrides_all(self):
        """CRITICAL overrides any combination."""
        self.assertEqual(
            aggregate_severity(["CRITICAL", "HIGH", "MEDIUM", "LOW"]), "CRITICAL"
        )

    def test_high_overrides_medium_low(self):
        """HIGH overrides MEDIUM and LOW."""
        self.assertEqual(aggregate_severity(["MEDIUM", "HIGH", "LOW"]), "HIGH")

    def test_medium_overrides_low(self):
        """MEDIUM overrides LOW."""
        self.assertEqual(aggregate_severity(["LOW", "MEDIUM"]), "MEDIUM")


if __name__ == "__main__":
    unittest.main()
