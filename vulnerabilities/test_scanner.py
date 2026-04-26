"""Tests for the scan pipeline orchestrator and concrete implementations."""

import unittest

from scanner import (
    MockDerivationSource,
    MockVulnerabilityScanner,
    MockDependencyMapper,
    TreeMergerImpl,
    TreeNormalizerImpl,
    ScanPipeline,
)
from interfaces import (
    DerivationSource,
    VulnerabilityScanner,
    DependencyMapper,
    TreeMerger,
    TreeNormalizer,
)


class TestMockDerivationSource(unittest.TestCase):
    """Test MockDerivationSource implementation."""

    def test_show_derivation_returns_dict(self):
        """show_derivation returns a dict with demo derivation."""
        source = MockDerivationSource()
        result = source.show_derivation("/run/current-system")
        self.assertIsInstance(result, dict)
        self.assertIn("/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv", result)


class TestMockVulnerabilityScanner(unittest.TestCase):
    """Test MockVulnerabilityScanner implementation."""

    def test_scan_returns_vulnerabilities(self):
        """scan_vulnerabilities returns demo vulnerabilities."""
        scanner = MockVulnerabilityScanner()
        result = scanner.scan_vulnerabilities("/nix/store/test.drv")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        pnames = {v["pname"] for v in result}
        self.assertIn("Diff", pnames)
        self.assertIn("ShellCheck", pnames)


class TestMockDependencyMapper(unittest.TestCase):
    """Test MockDependencyMapper implementation."""

    def test_why_depends_returns_trees(self):
        """why_depends returns dependency trees for known derivation pair."""
        mapper = MockDependencyMapper()
        system = "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv"
        target = "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv"
        result = mapper.why_depends(system, target)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)


class TestTreeMergerImpl(unittest.TestCase):
    """Test TreeMergerImpl implementation."""

    def test_merge_empty_returns_empty(self):
        """Merging empty list returns empty dict."""
        merger = TreeMergerImpl()
        result = merger.merge_trees([])
        self.assertEqual(result, {})

    def test_merge_single_tree(self):
        """Merging single tree returns a dict."""
        merger = TreeMergerImpl()
        trees = [{"drv_path": "/nix/store/a.drv", "pname": "a", "children": []}]
        result = merger.merge_trees(trees)
        self.assertIsInstance(result, dict)


class TestTreeNormalizerImpl(unittest.TestCase):
    """Test TreeNormalizerImpl implementation."""

    def test_normalize_with_mock_lookup(self):
        """Normalizing with default mock lookup finds vulnerabilities."""
        normalizer = TreeNormalizerImpl()
        tree = {
            "pname": "Diff",
            "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
            "children": [],
        }
        result = normalizer.normalize(tree)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["package_name"], "Diff")
        self.assertEqual(result[0]["severity"], "CRITICAL")

    def test_normalize_with_custom_lookup(self):
        """Normalizing with custom lookup uses provided function."""
        def custom_lookup(pname, drv_path):
            if pname == "CustomPkg":
                return {"cvssv3_basescore": {"CVE-2025-0001": 7.5}}
            return {}

        normalizer = TreeNormalizerImpl(vuln_lookup=custom_lookup)
        tree = {
            "pname": "CustomPkg",
            "drv_path": "/nix/store/custom.drv",
            "children": [],
        }
        result = normalizer.normalize(tree)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["severity"], "HIGH")

    def test_normalize_empty_tree(self):
        """Normalizing empty tree returns no records."""
        normalizer = TreeNormalizerImpl()
        result = normalizer.normalize({})
        self.assertEqual(result, [])


class TestScanPipeline(unittest.TestCase):
    """Test ScanPipeline orchestrator."""

    def test_default_creates_pipeline(self):
        """default() creates a pipeline with all mock implementations."""
        pipeline = ScanPipeline.default()
        self.assertIsInstance(pipeline.derivation_source, MockDerivationSource)
        self.assertIsInstance(pipeline.vulnerability_scanner, MockVulnerabilityScanner)
        self.assertIsInstance(pipeline.dependency_mapper, MockDependencyMapper)
        self.assertIsInstance(pipeline.tree_merger, TreeMergerImpl)
        self.assertIsInstance(pipeline.tree_normalizer, TreeNormalizerImpl)

    def test_run_scan_returns_results(self):
        """run_scan returns vulnerability results."""
        pipeline = ScanPipeline.default()
        result = pipeline.run_scan("/run/current-system")
        self.assertNotIn("error", result)
        self.assertEqual(result["vulnerabilities_found"], 2)
        self.assertEqual(result["target"], "/run/current-system")
        pnames = {v["package_name"] for v in result["vulnerabilities"]}
        self.assertIn("Diff", pnames)
        self.assertIn("ShellCheck", pnames)

    def test_run_scan_no_derivation_returns_error(self):
        """run_scan returns error when no derivation found."""
        pipeline = ScanPipeline.default()
        # Override the derivation source to return empty
        pipeline.derivation_source = MockDerivationSource()
        original_show = pipeline.derivation_source.show_derivation
        pipeline.derivation_source.show_derivation = lambda target: {}
        result = pipeline.run_scan("/nonexistent")
        self.assertIn("error", result)


class TestScanPipelineWithCustomStages(unittest.TestCase):
    """Test ScanPipeline with custom (mocked) stages."""

    def test_run_scan_with_custom_stages(self):
        """run_scan works with custom stage implementations."""
        # Create custom mock stages
        class CustomDerivationSource(DerivationSource):
            def show_derivation(self, target):
                return {"/nix/store/custom.drv": {}}

        class CustomVulnerabilityScanner(VulnerabilityScanner):
            def scan_vulnerabilities(self, target):
                return [{"pname": "CustomVuln", "derivation": "/nix/store/vuln.drv", "cvssv3_basescore": {"CVE-2025-0002": 5.0}}]

        class CustomDependencyMapper(DependencyMapper):
            def why_depends(self, system, target):
                return [{"drv_path": system, "pname": "root", "children": [{"drv_path": target, "pname": "vuln", "children": []}]}]

        class CustomTreeMerger(TreeMerger):
            def merge_trees(self, trees):
                return {"drv_path": "/nix/store/merged.drv", "pname": "merged", "children": []}

        class CustomTreeNormalizer(TreeNormalizer):
            def normalize(self, tree, vuln_lookup=None):
                return [{"package_name": "merged", "drv_path": "/nix/store/merged.drv", "severity": "LOW"}]

        pipeline = ScanPipeline(
            derivation_source=CustomDerivationSource(),
            vulnerability_scanner=CustomVulnerabilityScanner(),
            dependency_mapper=CustomDependencyMapper(),
            tree_merger=CustomTreeMerger(),
            tree_normalizer=CustomTreeNormalizer(),
        )
        result = pipeline.run_scan("/custom/target")
        self.assertEqual(result["vulnerabilities_found"], 1)
        self.assertEqual(result["vulnerabilities"][0]["package_name"], "merged")


if __name__ == "__main__":
    unittest.main()
