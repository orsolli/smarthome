"""Tests for core/identity module."""

import unittest

from core.identity import version_from_drv, compressed_lineages


class TestVersionFromDrv(unittest.TestCase):
    """Version of a derivation: everything after the base package name."""

    def test_plain_version(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/gccdrv00000000000000000000000000000-gcc-9.99.0.drv", "gcc"
            ),
            "9.99.0",
        )

    def test_version_with_variant_suffix(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/gccdrv00000000000000000000000000000-gcc-9.99.0-src.drv", "gcc"
            ),
            "9.99.0-src",
        )

    def test_package_name_already_carries_the_version(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/glcdrv00000000000000000000000000000-glibc-9.99-11.drv",
                "glibc-2.42",
            ),
            "9.99-11",
        )

    def test_multiword_package_name(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/locdrv000000000000000000000000000000-glibc-locales-9.99-22.drv",
                "glibc-locales-2.42",
            ),
            "9.99-22",
        )

    def test_derivation_without_version(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/stddrv000000000000000000000000000000-stdenv-linux.drv",
                "stdenv-linux",
            ),
            "",
        )

    def test_name_containing_digits(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/abcdefghijklmnopqrstuvwxyz01234567-python3-3.12.7.drv",
                "python3",
            ),
            "3.12.7",
        )

    def test_abi_suffix_belongs_to_the_version(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/wkddrv000000000000000000000000000000-webkitgtk-9.99.0+abi=1.0.drv",
                "webkitgtk",
            ),
            "9.99.0+abi=1.0",
        )

    def test_package_name_does_not_match_path(self):
        self.assertEqual(
            version_from_drv(
                "/nix/store/abcdefghijklmnopqrstuvwxyz01234567-pigzip.drv", "gzip"
            ),
            "",
        )

    def test_path_without_store_hash(self):
        self.assertEqual(version_from_drv("/nix/store/system.drv", "system"), "")


class TestCompressedLineages(unittest.TestCase):
    """Lineage keys anchor at the nearest unambiguous ancestor."""

    def setUp(self):
        self.nodes = [
            {"id": 1, "package_name": "nixos-system-example", "parent_id": None},
            {"id": 2, "package_name": "system-path", "parent_id": 1},
            {"id": 3, "package_name": "curl", "parent_id": 2},
            {"id": 4, "package_name": "stdenv-linux", "parent_id": 2},
            {"id": 5, "package_name": "gcc", "parent_id": 4},
            {"id": 6, "package_name": "gcc", "parent_id": 4},
            {"id": 7, "package_name": "gzip", "parent_id": 5},
        ]
        self.lineages = compressed_lineages(self.nodes, "/run/current-system")

    def test_root_is_the_target(self):
        self.assertEqual(self.lineages[1], "/run/current-system")

    def test_unambiguous_ancestor_used(self):
        self.assertEqual(self.lineages[3], "/run/current-system/system-path/curl")
        self.assertEqual(self.lineages[4], "/run/current-system/system-path/stdenv-linux")

    def test_duplicate_names_share_the_lineage_of_their_parent(self):
        self.assertEqual(self.lineages[5], "/run/current-system/stdenv-linux/gcc")
        self.assertEqual(self.lineages[6], "/run/current-system/stdenv-linux/gcc")

    def test_ambiguous_names_are_skipped(self):
        # gcc occurs twice, so gzip's lineage starts at stdenv-linux
        self.assertEqual(self.lineages[7], "/run/current-system/stdenv-linux/gcc/gzip")

    def test_no_unique_ancestor_falls_back_to_first_level(self):
        nodes = [
            {"id": 1, "package_name": "root", "parent_id": None},
            {"id": 2, "package_name": "a", "parent_id": 1},
            {"id": 3, "package_name": "a", "parent_id": 1},
            {"id": 4, "package_name": "b", "parent_id": 2},
        ]
        self.assertEqual(compressed_lineages(nodes, "./result")[4], "./result/a/b")

    def test_every_node_gets_a_lineage(self):
        self.assertEqual(len(self.lineages), len(self.nodes))
        self.assertTrue(all(lineage for lineage in self.lineages.values()))


if __name__ == "__main__":
    unittest.main()
