"""Tests for app/colors.py: the severity -> CSS map the templates paint with."""

import unittest

from app.colors import SEVERITY_COLORS
from core.severity import SEVERITY_RANK, severity_bg_color, severity_color


class TestSeverityColors(unittest.TestCase):
    """The map covers every severity, in rank order."""

    def test_every_severity_has_a_color_and_a_tint(self):
        self.assertEqual(set(SEVERITY_COLORS), set(SEVERITY_RANK))
        for colors in SEVERITY_COLORS.values():
            self.assertEqual(len(colors), 2)

    def test_the_map_follows_the_severity_order(self):
        """Templates iterate it to build the CSS, so order is the ranking."""
        self.assertEqual(list(SEVERITY_COLORS), list(SEVERITY_RANK))

    def test_the_values_come_from_core_severity(self):
        """No color is defined twice: the map is derived, not hand-written."""
        for severity in SEVERITY_RANK:
            self.assertEqual(
                SEVERITY_COLORS[severity],
                (severity_color(severity), severity_bg_color(severity)),
            )

    def test_an_unknown_severity_is_not_in_the_map(self):
        self.assertNotIn("BOGUS", SEVERITY_COLORS)


if __name__ == "__main__":
    unittest.main()
