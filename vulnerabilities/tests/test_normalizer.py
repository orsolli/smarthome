"""Tests for normalizer module."""

import unittest

from mock.mock_vulnix import MockVulnerabilityScanner
from core.normalizer import (
    TreeNormalizerImpl,
    _severity_from_cvss,
    _cvss_from_severity,
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


class TestCvssFromSeverity(unittest.TestCase):
    def test_critical(self):
        self.assertEqual(_cvss_from_severity("CRITICAL"), 9.0)

    def test_high(self):
        self.assertEqual(_cvss_from_severity("HIGH"), 7.0)

    def test_medium(self):
        self.assertEqual(_cvss_from_severity("MEDIUM"), 4.0)

    def test_low(self):
        self.assertEqual(_cvss_from_severity("LOW"), 0.1)

    def test_none(self):
        self.assertEqual(_cvss_from_severity("NONE"), 0.0)

    def test_unknown(self):
        self.assertEqual(_cvss_from_severity("UNKNOWN"), 0.0)


def _make_vuln_lookup():
    """Create a vulnerability lookup function from demo data."""
    vulns = MockVulnerabilityScanner().scan_vulnerabilities("/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv")
    
    return {v.get("derivation"): v for v in vulns}


class TestNormalizeTree(unittest.TestCase):
    def setUp(self):
        self.lookup = _make_vuln_lookup()

    def test_empty_tree(self):
        """Empty tree returns no records."""
        result = TreeNormalizerImpl().normalize({}, vuln_map=self.lookup)
        self.assertEqual(result, [])

    def test_vulnerable_node(self):
        """A vulnerable node produces a record."""
        tree = {
            "pname": "Diff",
            "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
            "children": [],
        }
        result = TreeNormalizerImpl().normalize(tree, vuln_map=self.lookup)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["package_name"], "Diff")
        self.assertEqual(result[0]["severity"], "CRITICAL")
        self.assertIn("severity_score", result[0])
        self.assertEqual(result[0]["severity_score"], 9.1)

    def test_severity_score_critical(self):
        """CVSS 9.1 maps to severity_score 9.1."""
        custom = {
            "/nix/store/crit.drv": {"cvssv3_basescore": {"CVE-2025-0001": 9.1}}
        }
        tree = {
            "pname": "CritPkg",
            "drv_path": "/nix/store/crit.drv",
            "children": [],
        }
        result = TreeNormalizerImpl().normalize(tree, vuln_map=custom)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["severity_score"], 9.1)

    def test_severity_score_none(self):
        """Non-vulnerable node has no severity_score."""
        tree = {
            "pname": "clean-pkg",
            "drv_path": "/nix/store/clean.drv",
            "children": [],
        }
        result = TreeNormalizerImpl().normalize(tree, vuln_map=self.lookup)
        self.assertEqual(result, [])

    def test_clean_node(self):
        """A non-vulnerable node produces no record."""
        tree = {
            "pname": "clean-pkg",
            "drv_path": "/nix/store/clean.drv",
            "children": [],
        }
        result = TreeNormalizerImpl().normalize(tree, vuln_map=self.lookup)
        self.assertEqual(result, [])

    def test_nested_vulnerable_nodes(self):
        """Nested vulnerable nodes produce multiple records."""
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
        result = TreeNormalizerImpl().normalize(tree, vuln_map=self.lookup)
        self.assertEqual(len(result), 2)
        pnames = {r["package_name"] for r in result}
        self.assertIn("ShellCheck", pnames)
        self.assertIn("Diff", pnames)
        for r in result:
            self.assertIn("severity_score", r)


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
