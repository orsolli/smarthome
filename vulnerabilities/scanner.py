"""Concrete implementations of pipeline interfaces and the scan pipeline orchestrator.

This module provides:
- Concrete implementations of each pipeline stage interface
- ScanPipeline: orchestrates the full scan workflow
- Default factory functions for creating instances with mock or production backends
"""

from typing import Any

from interfaces import (
    DependencyMapper,
    DerivationSource,
    TreeMerger,
    TreeNormalizer,
    VulnerabilityScanner,
)
from merger import merge_dependency_trees
from mock_derivation import show_derivation
from mock_vulnix import scan_vulnerabilities as _mock_scan_vuln
from mock_why_depends import why_depends
from normalizer import normalize_tree as _normalize_tree
from normalizer import _find_vuln_info as _mock_find_vuln


# --- Concrete Implementations ---


class MockDerivationSource(DerivationSource):
    """Mock implementation of DerivationSource using mock_derivation."""

    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        return show_derivation(target)


class MockVulnerabilityScanner(VulnerabilityScanner):
    """Mock implementation of VulnerabilityScanner using mock_vulnix."""

    def scan_vulnerabilities(self, target: str) -> list[dict[str, Any]]:
        return _mock_scan_vuln(target)


class MockDependencyMapper(DependencyMapper):
    """Mock implementation of DependencyMapper using mock_why_depends."""

    def why_depends(
        self, system_derivation: str, target_derivation: str
    ) -> list[dict[str, Any]]:
        return why_depends(system_derivation, target_derivation)


class TreeMergerImpl(TreeMerger):
    """Implementation of TreeMerger using the merger module."""

    def merge_trees(self, dependency_trees: list[dict[str, Any]]) -> dict[str, Any]:
        return merge_dependency_trees(dependency_trees)


class TreeNormalizerImpl(TreeNormalizer):
    """Implementation of TreeNormalizer using the normalizer module.

    Receives vulnerability lookup via constructor so it does not
    depend on any specific mock or production scanner.
    """

    def __init__(self, vuln_lookup=None):
        """Initialize with an optional vulnerability lookup function.

        Args:
            vuln_lookup: Callable(pname, drv_path) -> dict. If None,
                defaults to the mock lookup function.
        """
        self._vuln_lookup = vuln_lookup or _mock_find_vuln

    def normalize(
        self,
        tree: dict[str, Any],
        vuln_lookup: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return _normalize_tree(tree, vuln_lookup or self._vuln_lookup)


# --- Pipeline Orchestrator ---


class ScanPipeline:
    """Orchestrates the full vulnerability scan workflow.

    Takes dependency-injected pipeline stages and runs them in sequence:
    1. DerivationSource: resolve target to derivation
    2. VulnerabilityScanner: scan for vulnerabilities
    3. DependencyMapper: get dependency trees for each vuln
    4. TreeMerger: merge all trees into one
    5. TreeNormalizer: convert to flat vulnerability records

    Usage:
        pipeline = ScanPipeline.default()
        result = pipeline.run_scan("/run/current-system")
    """

    def __init__(
        self,
        derivation_source: DerivationSource,
        vulnerability_scanner: VulnerabilityScanner,
        dependency_mapper: DependencyMapper,
        tree_merger: TreeMerger,
        tree_normalizer: TreeNormalizer,
    ):
        """Initialize with injected pipeline stages.

        Args:
            derivation_source: Resolves target to derivation.
            vulnerability_scanner: Scans derivation for vulns.
            dependency_mapper: Maps vulns to dependency trees.
            tree_merger: Merges multiple trees into one.
            tree_normalizer: Normalizes tree to flat records.
        """
        self.derivation_source = derivation_source
        self.vulnerability_scanner = vulnerability_scanner
        self.dependency_mapper = dependency_mapper
        self.tree_merger = tree_merger
        self.tree_normalizer = tree_normalizer

    @classmethod
    def default(cls) -> "ScanPipeline":
        """Create a pipeline with all mock implementations.

        Returns:
            A ScanPipeline configured for development.
        """
        return cls(
            derivation_source=MockDerivationSource(),
            vulnerability_scanner=MockVulnerabilityScanner(),
            dependency_mapper=MockDependencyMapper(),
            tree_merger=TreeMergerImpl(),
            tree_normalizer=TreeNormalizerImpl(),
        )

    def run_scan(self, target: str) -> dict[str, Any]:
        """Run a full vulnerability scan on the given target.

        Steps:
            1. Resolve derivation via DerivationSource
            2. Scan for vulnerabilities via VulnerabilityScanner
            3. Map dependencies via DependencyMapper
            4. Merge trees via TreeMerger
            5. Normalize to flat records via TreeNormalizer

        Args:
            target: The derivation path to scan.

        Returns:
            Dict with scan results summary.
        """
        # Step 1: Resolve derivation
        derivations = self.derivation_source.show_derivation(target)
        system_derivation = next(iter(derivations), None)
        if not system_derivation:
            return {"error": "No derivation found for target", "target": target}

        # Step 2: Scan for vulnerabilities
        vulns = self.vulnerability_scanner.scan_vulnerabilities(system_derivation)

        # Step 3: Get dependency trees for each vulnerability
        dep_trees: list[dict[str, Any]] = []
        for vuln in vulns:
            drv = vuln.get("derivation", "")
            tree = self.dependency_mapper.why_depends(system_derivation, drv)
            dep_trees.extend(tree)

        # Step 4: Merge trees
        merged = self.tree_merger.merge_trees(dep_trees)

        # Step 5: Normalize to flat records
        records = self.tree_normalizer.normalize(merged)

        return {
            "scan_id": None,  # Set by caller after DB insertion
            "target": target,
            "vulnerabilities_found": len(records),
            "vulnerabilities": records,
        }
