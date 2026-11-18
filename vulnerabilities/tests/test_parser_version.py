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

    def test_version_with_equals_sign(self):
        """webkitgtk-9.99.0+abi=1.0.drv → ('webkitgtk', '9.99.0+abi=1.0').

        The ABI variant is part of the version, not of the package name: the
        same package rebuilt with a different ABI must still be one node.
        """
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path(
            "/nix/store/wkddrv000000000000000000000000000000-webkitgtk-9.99.0+abi=1.0.drv"
        )
        self.assertEqual(name, "webkitgtk")
        self.assertEqual(version, "9.99.0+abi=1.0")

    def test_version_with_revision_suffix(self):
        """glibc-9.99-11.drv → ('glibc', '9.99-11')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/glcdrv00000000000000000000000000000-glibc-9.99-11.drv")
        self.assertEqual(name, "glibc")
        self.assertEqual(version, "9.99-11")

    def test_name_with_plus_sign_and_digits(self):
        """gtk+3.drv → ('gtk+3', ''). No dash precedes the digits, so there is no version."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/abcdefghijklmnopqrstuvwxyz012345-gtk+3.drv")
        self.assertEqual(name, "gtk+3")
        self.assertEqual(version, "")

    def test_derivation_without_version_but_with_dashes(self):
        """pre-switch-checks.drv → ('pre-switch-checks', '')."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path("/nix/store/chkdrv100000000000000000000000000000-pre-switch-checks.drv")
        self.assertEqual(name, "pre-switch-checks")
        self.assertEqual(version, "")

    def test_generation_stamp_is_the_version(self):
        """...-nixos-system-x86_64-linux.nixos-24_11_20241201_abcdef0.drv splits at the stamp."""
        from core.parser import _extract_name_from_path
        name, version = _extract_name_from_path(
            "/nix/store/gendrv00000000000000000000000000000-nixos-system-x86_64-linux.nixos-24_11_20241201_abcdef0.drv"
        )
        self.assertEqual(name, "nixos-system-x86_64-linux.nixos")
        self.assertEqual(version, "24_11_20241201_abcdef0")


if __name__ == "__main__":
    import sys
    sys.path.append(__import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..")))
    unittest.main()
