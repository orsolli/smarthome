"""Interface definitions for the vulnerability scan pipeline.

Each pipeline stage is defined as an Abstract Base Class (ABC) with an
Interface suffix. Implementations are injected at runtime (dependency
injection), allowing mock implementations for development and real
implementations for production.

This mirrors the interface pattern used by the tree_parser library.
"""

from abc import ABC, abstractmethod
from typing import Any


class VulnerabilityScannerInterface(ABC):
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


class DependencyMapperInterface(ABC):
    """Maps why a vulnerable package depends on the system.

    Usage:
        mapper = DependencyMapperImpl()
        trees = mapper.why_depends(system_derivation, vuln_derivation)
    """

    @abstractmethod
    def why_depends(
        self, system_derivation: str, target_derivation: str
    ) -> list[dict[str, Any]] | str:
        """Get the dependency tree from system to the target derivation.

        Args:
            system_derivation: The root system derivation path.
            target_derivation: The target derivation to trace dependencies for.

        Returns:
            A concatenated list of of dependency tree strings.
        """
        ...


class TreeMergerInterface(ABC):
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


class TreeNormalizerInterface(ABC):
    """Converts a merged dependency tree into flat vulnerability records.

    Receives vulnerability info via constructor injection so it does not
    depend on any specific mock or production scanner.

    Usage:
        normalizer = TreeNormalizerImpl(vuln_map)
        records = normalizer.normalize(merged_tree)
    """

    @abstractmethod
    def normalize(
        self,
        tree: dict[str, Any],
        vuln_map: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Convert a dependency tree into flat vulnerability records.

        Args:
            tree: A merged dependency tree dict.
            vuln_map: Dict mapping drv_path to vulnerability info.

        Returns:
            List of dicts with keys: package_name, drv_path, severity.
        """
        ...


class StorageInterface(ABC):
    """Handles persistence of scan results and dependency trees.

    Usage:
        storage = DatabaseStorageImpl(db_path)
        scan_id = storage.insert_scan(target)
    """

    @abstractmethod
    def insert_scan(self, target: str) -> int:
        """Insert a scan record and return its ID.

        Args:
            target: The derivation path scanned.

        Returns:
            The ID of the inserted scan.
        """
        ...

    @abstractmethod
    def insert_vulnerability_event(
        self, scan_id: int, package_name: str, drv_path: str, severity: str
    ) -> int:
        """Insert a vulnerability event and return its ID.

        Args:
            scan_id: The ID of the scan.
            package_name: The name of the vulnerable package.
            drv_path: The Nix derivation path.
            severity: The severity level (e.g. 'HIGH').

        Returns:
            The ID of the inserted event.
        """
        ...

    @abstractmethod
    def insert_dependency_node(
        self,
        scan_id: int,
        package_name: str,
        drv_path: str,
        parent_id: int | None = None,
        child_id: int | None = None,
        vulnerability_event_id: int | None = None,
    ) -> int:
        """Insert a node into the dependency tree.

        Args:
            scan_id: The ID of the scan.
            package_name: The name of the package.
            drv_path: The Nix derivation path.
            parent_id: The ID of the parent node.
            child_id: The ID of the child node.
            vulnerability_event_id: The ID of the linked vulnerability event.

        Returns:
            The ID of the inserted node.
        """
        ...
