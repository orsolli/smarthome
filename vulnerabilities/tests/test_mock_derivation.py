"""Tests for mock_derivation module."""

import unittest
from mock.mock_derivation import MockDerivationSource


class TestMockDerivation(unittest.TestCase):
    def test_returns_demo_derivation(self):
        result = MockDerivationSource().show_derivation("/run/current-system")
        self.assertEqual(len(result), 1)
        expected_key = "sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv"
        self.assertIn(expected_key, result)

    def test_metadata_is_empty_dict(self):
        result = MockDerivationSource().show_derivation("/run/current-system")
        self.assertEqual(result[list(result.keys())[0]], {})


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
