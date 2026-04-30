"""Tests for mock_derivation module."""

import unittest
from mock.mock_derivation import show_derivation


class TestMockDerivation(unittest.TestCase):
    def test_returns_demo_derivation(self):
        result = show_derivation("/run/current-system")
        self.assertEqual(len(result), 1)
        expected_key = "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv"
        self.assertIn(expected_key, result)

    def test_metadata_is_empty_dict(self):
        result = show_derivation("/run/current-system")
        self.assertEqual(result[list(result.keys())[0]], {})


if __name__ == "__main__":
    unittest.main()
