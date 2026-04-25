"""Tests for mock_derivation module."""

import unittest
from vulnerabilities.mock_derivation import show_derivation


class TestMockDerivation(unittest.TestCase):
    def test_returns_demo_derivation(self):
        result = show_derivation("/run/current-system")
        self.assertEqual(len(result), 1)
        expected_key = "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv"
        self.assertIn(expected_key, result)

    def test_metadata_is_empty_dict(self):
        result = show_derivation("/run/current-system")
        self.assertEqual(result[list(result.keys())[0]], {})


if __name__ == "__main__":
    unittest.main()
