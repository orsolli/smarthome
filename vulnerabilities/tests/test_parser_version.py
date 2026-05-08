"""Tests for version-aware package name extraction.

TDD: write tests first, then implement _extract_name_from_path().
"""

import unittest


class TestExtractNameFromPath(unittest.TestCase):
    """Test _extract_name_from_path handles versioned and non-versioned names."""

    def test_standard_version(self):
        """ed-9.99.0.drv → ('ed', '9.99.0')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/xyz-ed-9.99.0.drv")
        self.assertEqual(name, "ed")
        self.assertEqual(version, "9.99.0")

    def test_version_with_rc(self):
        """some-lib-1.0-rc1.drv → ('some-lib', '1.0-rc1')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/xyz-some-lib-1.0-rc1.drv")
        self.assertEqual(name, "some-lib")
        self.assertEqual(version, "1.0-rc1")

    def test_no_version(self):
        """some-lib.drv → ('some-lib', '')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/xyz-some-lib.drv")
        self.assertEqual(name, "some-lib")
        self.assertEqual(version, "")

    def test_no_version_dashes(self):
        """some-lib-with-dashes.drv → ('some-lib-with-dashes', '')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/xyz-some-lib-with-dashes.drv")
        self.assertEqual(name, "some-lib-with-dashes")
        self.assertEqual(version, "")

    def test_nix_hash_stripped(self):
        """vulndrv0000000000000000000000000000-vulnerabilities-0.1.drv → ('vulnerabilities', '0.1')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/vulndrv0000000000000000000000000000-vulnerabilities-0.1.drv")
        self.assertEqual(name, "vulnerabilities")
        self.assertEqual(version, "0.1")


if __name__ == "__main__":
    import sys
    sys.path.append(__import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..")))
    unittest.main()
