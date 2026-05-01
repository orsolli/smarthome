"""Tests for the scan pipeline orchestrator and concrete implementations."""

import os
import tempfile
import unittest

from core.orchestrator import TreeOrchestrator
from core.scanner import (
    MockDerivationSource,
    MockVulnerabilityScanner,
    MockDependencyMapper,
    TreeMergerImpl,
    TreeNormalizerImpl,
    ScanPipeline,
    MockStorage,
)
from interfaces import (
    DerivationSourceInterface,
    VulnerabilityScannerInterface,
    DependencyMapperInterface,
    TreeMergerInterface,
    TreeOrchestratorInterface,
    TreeNormalizerInterface,
    StorageInterface,
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
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestTreeMergerImpl(unittest.TestCase):
    """Test TreeMergerImpl implementation."""

    def test_merge_empty_returns_empty(self):
        """Merging empty list returns empty dict."""
        merger = TreeMergerImpl()
        result = merger.merge_trees([])
        self.assertEqual(result, {'children': [], 'name': '.', 'type': 'directory'})

    def test_merge_single_tree(self):
        """Merging single tree returns a dict."""
        merger = TreeMergerImpl()
        trees = [{"drv_path": "/nix/store/a.drv", "name": "a-1", "pname": "a", "children": []}]
        result = merger.merge_trees(trees)
        self.assertIsInstance(result, dict)


class TestTreeNormalizerImpl(unittest.TestCase):
    """Test TreeNormalizerImpl implementation."""

    def _make_vuln_map(self, vulns):
        return {v['derivation']: v for v in vulns}

    def test_normalize_with_mock_lookup(self):
        """Normalizing with default mock lookup finds vulnerabilities."""
        from mock.mock_vulnix import MockVulnerabilityScanner
        vulns = MockVulnerabilityScanner().scan_vulnerabilities("")
        normalizer = TreeNormalizerImpl()
        tree = {
            "pname": "Diff",
            "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
            "children": [],
        }
        result = normalizer.normalize(tree, vuln_map=self._make_vuln_map(vulns))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["package_name"], "Diff")
        self.assertEqual(result[0]["severity"], "CRITICAL")

    def test_normalize_with_custom_lookup(self):
        """Normalizing with custom lookup uses provided function."""
        custom_lookup = {
            "/nix/store/custom.drv":{"cvssv3_basescore": {"CVE-2025-0001": 7.5}}
        }

        normalizer = TreeNormalizerImpl()
        tree = {
            "pname": "CustomPkg",
            "drv_path": "/nix/store/custom.drv",
            "children": [],
        }
        result = normalizer.normalize(tree, vuln_map=custom_lookup)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["severity"], "HIGH")

    def test_normalize_empty_tree(self):
        """Normalizing empty tree returns no records."""
        normalizer = TreeNormalizerImpl()
        result = normalizer.normalize({}, vuln_map={})
        self.assertEqual(result, [])


class TestMockStorage(unittest.TestCase):
    """Test MockStorage implementation."""

    def test_insert_scan(self):
        """insert_scan returns incrementing IDs."""
        storage = MockStorage()
        id1 = storage.insert_scan("target1")
        id2 = storage.insert_scan("target2")
        self.assertEqual(id1, 1)
        self.assertEqual(id2, 2)

    def test_insert_vulnerability_event(self):
        """insert_vulnerability_event returns incrementing IDs."""
        storage = MockStorage()
        # MockStorage starts counter at 1; insert_scan uses ID 1
        storage.insert_scan("target")  # consumes ID 1
        eid1 = storage.insert_vulnerability_event(1, "pkg1", "/drv1", "HIGH")
        eid2 = storage.insert_vulnerability_event(1, "pkg2", "/drv2", "LOW")
        self.assertEqual(eid1, 2)
        self.assertEqual(eid2, 3)

    def test_insert_dependency_node(self):
        """insert_dependency_node returns incrementing IDs."""
        storage = MockStorage()
        storage.insert_scan("target")  # consumes ID 1
        eid1 = storage.insert_vulnerability_event(1, "pkg1", "/drv1", "HIGH")
        eid2 = storage.insert_vulnerability_event(1, "pkg2", "/drv2", "LOW")
        nid = storage.insert_dependency_node(1, "pkg", "/drv")
        self.assertEqual(nid, 4)  # IDs 1-3 consumed by insert_scan and insert_vulnerability_event in MockStorage default


class TestScanPipeline(unittest.TestCase):
    """Test ScanPipeline orchestrator."""

    def test_default_creates_pipeline(self):
        """default() creates a pipeline with all mock implementations."""
        pipeline = ScanPipeline.default()
        self.assertIsInstance(pipeline.derivation_source, MockDerivationSource)
        self.assertIsInstance(pipeline.vulnerability_scanner, MockVulnerabilityScanner)
        self.assertIsInstance(pipeline.dependency_mapper, MockDependencyMapper)
        self.assertIsInstance(pipeline.orchestrator, TreeOrchestrator)
        self.assertIsInstance(pipeline.tree_normalizer, TreeNormalizerImpl)
        self.assertIsInstance(pipeline.storage, MockStorage)

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
        pipeline.derivation_source.show_derivation = lambda target: {}
        result = pipeline.run_scan("/nonexistent")
        self.assertIn("error", result)


class TestScanPipelineWithCustomStages(unittest.TestCase):
    """Test ScanPipeline with custom (mocked) stages."""

    def test_run_scan_with_custom_stages(self):
        """run_scan works with custom stage implementations."""
        class CustomDerivationSource(DerivationSourceInterface):
            def show_derivation(self, target):
                return {"/nix/store/custom.drv": {}}

        class CustomVulnerabilityScanner(VulnerabilityScannerInterface):
            def scan_vulnerabilities(self, target):
                return [{"pname": "CustomVuln", "derivation": "/nix/store/vuln.drv", "cvssv3_basescore": {"CVE-2025-0002": 5.0}}]

        class CustomDependencyMapper(DependencyMapperInterface):
            def why_depends(self, system, target):
                return [{"drv_path": system, "pname": "root", "children": [{"drv_path": target, "pname": "vuln", "children": []}]}]

        class CustomTreeOrchestrator(TreeOrchestratorInterface):
            def process_tree_output(self, trees):
                return {"drv_path": "/nix/store/merged.drv", "name": "merged", "children": []}

        class CustomTreeNormalizer(TreeNormalizerInterface):
            def normalize(self, tree, vuln_map=None):
                return [{"package_name": "merged", "drv_path": "/nix/store/merged.drv", "severity": "LOW"}]

        class CustomStorage(StorageInterface):
            def __init__(self):
                self._next = 1
            def _next_id(self):
                current = self._next
                self._next += 1
                return current
            def insert_scan(self, target):
                return self._next_id()
            def insert_vulnerability_event(self, scan_id, package_name, drv_path, severity):
                return self._next_id()
            def insert_dependency_node(self, scan_id, package_name, drv_path, parent_id=None, child_id=None, vulnerability_event_id=None):
                return self._next_id()

        pipeline = ScanPipeline(
            derivation_source=CustomDerivationSource(),
            vulnerability_scanner=CustomVulnerabilityScanner(),
            dependency_mapper=CustomDependencyMapper(),
            orchestrator=CustomTreeOrchestrator(),
            tree_normalizer=CustomTreeNormalizer(),
            storage=CustomStorage(),
        )
        result = pipeline.run_scan("/custom/target")
        self.assertEqual(result["vulnerabilities_found"], 1)
        self.assertEqual(result["vulnerabilities"][0]["package_name"], "merged")


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()
