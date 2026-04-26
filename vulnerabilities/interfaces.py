"""Interface definitions for the vulnerability scan pipeline.

Each pipeline stage is defined as an Abstract Base Class (ABC).
Implementations are injected at runtime (dependency injection),
allowing mock implementations for development and real implementations
for production.

This mirrors the interface pattern used by the tree_parser library.
"""

from abc import ABC, abstractmethod
from typing import Any


class DerivationSource(ABC):
    """Resolves a target path to its Nix derivation.

    Usage:
        source = DerivationSourceImpl()
        derivations = source.show_derivation("/run/current-system")
    """

    @abstractmethod
    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        """Resolve target to its derivation dict.

        Args:
            target: The derivation path to resolve (e.g. /run/current-system).

        Returns:
            A dict mapping derivation paths to their metadata.
        """
        ...


class VulnerabilityScanner(ABC):
    """Scans a derivation for known vulnerabilities.

    Usage:
        scanner = VulnerabilityScannerImpl()
        vulns = scanner.scan_vulnerabilities("/nix/store/...-system.drv")
    """

    @abstractmethod
    def scan_vulnerabilities(self, target: str) -> list[dict[str, Any]]:
        """Scan a derivation for vulnerabilities.

        Args:
            target: The derivation path to scan.

        Returns:
            A list of vulnerability records with keys like pname,
            derivation, cvssv3_basescore, affected_by.
        """
        ...


class DependencyMapper(ABC):
    """Maps why a vulnerable package depends on the system.

    Usage:
        mapper = DependencyMapperImpl()
        trees = mapper.why_depends(system_derivation, vuln_derivation)
    """

    @abstractmethod
    def why_depends(
        self, system_derivation: str, target_derivation: str
    ) -> list[dict[str, Any]]:
        """Get the dependency tree from system to the target derivation.

        Args:
            system_derivation: The root system derivation path.
            target_derivation: The target derivation to trace dependencies for.

        Returns:
            A list of dependency tree dicts.
        """
        ...


class TreeMerger(ABC):
    """Merges multiple dependency trees into a single consolidated tree.

    Usage:
        merger = TreeMergerImpl()
        merged = merger.merge_trees([tree_a, tree_b])
    """

    @abstractmethod
    def merge_trees(self, dependency_trees: list[dict[str, Any]]) -> dict[str, Any]:
        """Merge multiple dependency trees into one.

        Args:
            dependency_trees: List of tree dicts from DependencyMapper.

        Returns:
            A consolidated tree dict with overlapping paths merged.
        """
        ...


class TreeNormalizer(ABC):
    """Converts a merged dependency tree into flat vulnerability records.

    Receives vulnerability info via constructor injection so it does not
    depend on any specific mock or production scanner.

    Usage:
        normalizer = TreeNormalizerImpl(vuln_lookup)
        records = normalizer.normalize(merged_tree)
    """

    @abstractmethod
    def normalize(
        self,
        tree: dict[str, Any],
        vuln_lookup: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Convert a dependency tree into flat vulnerability records.

        Args:
            tree: A merged dependency tree dict.
            vuln_lookup: Dict mapping (pname, drv_path) to vulnerability info.

        Returns:
            List of dicts with keys: package_name, drv_path, severity.
        """
        ...
