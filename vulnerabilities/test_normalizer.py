"""Tests for normalizer module."""

import os
import unittest

from mock_vulnix import scan_vulnerabilities
from normalizer import (
    normalize_tree,
    _severity_from_cvss,
)


class TestSeverityFromCvss(unittest.TestCase):
    def test_critical_score(self):
        """CVSS >= 9.0 returns CRITICAL."""
        self.assertEqual(_severity_from_cvss(9.0), "CRITICAL")
        self.assertEqual(_severity_from_cvss(9.8), "CRITICAL")
        self.assertEqual(_severity_from_cvss(10.0), "CRITICAL")

    def test_high_score(self):
        """CVSS >= 7.0 and < 9.0 returns HIGH."""
        self.assertEqual(_severity_from_cvss(7.0), "HIGH")
        self.assertEqual(_severity_from_cvss(8.5), "HIGH")
        self.assertEqual(_severity_from_cvss(8.9), "HIGH")

    def test_medium_score(self):
        """CVSS >= 4.0 and < 7.0 returns MEDIUM."""
        self.assertEqual(_severity_from_cvss(4.0), "MEDIUM")
        self.assertEqual(_severity_from_cvss(5.5), "MEDIUM")
        self.assertEqual(_severity_from_cvss(6.9), "MEDIUM")

    def test_low_score(self):
        """CVSS < 4.0 returns LOW."""
        self.assertEqual(_severity_from_cvss(0.0), "LOW")
        self.assertEqual(_severity_from_cvss(3.9), "LOW")


class TestNormalizeTree(unittest.TestCase):
    def _make_vuln_lookup(self, vulns):
        """Create a vuln_lookup callable from a list of vulnix records."""
        def lookup(pname, drv_path):
            for v in vulns:
                if v.get("pname") == pname or v.get("derivation") == drv_path:
                    return v
            return {}
        return lookup

    def test_empty_tree(self):
        """Empty tree returns no records."""
        result = normalize_tree({}, vuln_lookup=self._make_vuln_lookup([]))
        self.assertEqual(result, [])

    def test_vulnerable_node(self):
        """A vulnerable node produces a record."""
        vulns = scan_vulnerabilities("")
        tree = {
            "pname": "Diff",
            "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
            "children": [],
        }
        result = normalize_tree(tree, vuln_lookup=self._make_vuln_lookup(vulns))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["package_name"], "Diff")
        self.assertEqual(result[0]["severity"], "CRITICAL")

    def test_clean_node(self):
        """A non-vulnerable node produces no record."""
        tree = {
            "pname": "clean-pkg",
            "drv_path": "/nix/store/clean.drv",
            "children": [],
        }
        result = normalize_tree(tree, vuln_lookup=self._make_vuln_lookup([]))
        self.assertEqual(result, [])

    def test_nested_vulnerable_nodes(self):
        """Nested vulnerable nodes produce multiple records."""
        vulns = scan_vulnerabilities("")
        tree = {
            "pname": "ShellCheck",
            "drv_path": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
            "children": [
                {
                    "pname": "Diff",
                    "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
                    "children": [],
                },
                {
                    "pname": "clean-pkg",
                    "drv_path": "/nix/store/clean.drv",
                    "children": [],
                },
            ],
        }
        result = normalize_tree(tree, vuln_lookup=self._make_vuln_lookup(vulns))
        self.assertEqual(len(result), 2)
        pnames = {r["package_name"] for r in result}
        self.assertIn("ShellCheck", pnames)
        self.assertIn("Diff", pnames)

    def test_deduplication(self):
        """Same (pname, drv_path) in multiple paths produces one record."""
        vulns = scan_vulnerabilities("")
        tree = {
            "pname": "Diff",
            "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
            "children": [
                {
                    "pname": "Diff",
                    "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
                    "children": [],
                },
            ],
        }
        result = normalize_tree(tree, vuln_lookup=self._make_vuln_lookup(vulns))
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
