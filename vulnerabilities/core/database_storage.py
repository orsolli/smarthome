"""Database implementation of the StorageInterface.

Wraps database.py functions to provide a concrete implementation
of the StorageInterface for the scan pipeline.
"""

import sqlite3

from interfaces import StorageInterface
from core import database


class DatabaseStorage(StorageInterface):
    """Concrete implementation of StorageInterface backed by SQLite.

    Usage:
        storage = DatabaseStorage(db_path)
        scan_id = storage.insert_scan(target)
    """

    def __init__(self, db_path: str):
        """Initialize with a database path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = database.init_db(db_path)

    def insert_scan(
        self,
        target: str,
        timestamp: str | None = None,
        scanned_path: str | None = None,
    ) -> int:
        """Insert a scan record and return its ID.

        Args:
            target: The identity of what was scanned.
            timestamp: ISO timestamp, defaults to now.
            scanned_path: The derivation path actually handed to vulnix,
                which differs from the target when an old generation is
                scanned under an alias. Defaults to the target.

        Returns:
            The ID of the inserted scan.
        """
        return database.insert_scan(self.conn, target, timestamp, scanned_path)

    def insert_vulnerability_event(
        self,
        scan_id: int,
        package_name: str,
        drv_path: str,
        severity: str,
        version: str | None = None,
        timestamp: str | None = None,
    ) -> int:
        """Insert a vulnerability event and return its ID.

        Args:
            scan_id: The ID of the scan.
            package_name: The name of the vulnerable package.
            drv_path: The Nix derivation path.
            severity: The severity level (e.g. 'HIGH').
            version: Version of the vulnerable derivation.
            timestamp: When the scan ran, defaults to now.

        Returns:
            The ID of the inserted event.
        """
        return database.insert_vulnerability_event(
            self.conn, scan_id, package_name, drv_path, severity, version, timestamp
        )

    def insert_dependency_node(
        self,
        scan_id: int,
        package_name: str,
        drv_path: str,
        parent_id: int | None = None,
        child_id: int | None = None,
        vulnerability_event_id: int | None = None,
        version: str | None = None,
        lineage: str | None = None,
    ) -> int:
        """Insert a node into the dependency tree.

        Args:
            scan_id: The ID of the scan.
            package_name: The name of the package.
            drv_path: The Nix derivation path.
            parent_id: The ID of the parent node.
            child_id: The ID of the child node.
            vulnerability_event_id: The ID of the linked vulnerability event.
            version: Version of this derivation.
            lineage: Compressed lineage path of this node.

        Returns:
            The ID of the inserted node.
        """
        return database.insert_dependency_node(
            self.conn,
            scan_id,
            package_name,
            drv_path,
            parent_id=parent_id,
            child_id=child_id,
            vulnerability_event_id=vulnerability_event_id,
            version=version,
            lineage=lineage,
        )

    def update_dependency_node(
        self,
        id: int,
        scan_id: int | None = None,
        package_name: str | None = None,
        drv_path: str | None = None,
        parent_id: int | None = None,
        child_id: int | None = None,
        vulnerability_event_id: int | None = None,
        version: str | None = None,
        lineage: str | None = None,
    ) -> int:
        return database.update_dependency_node(
            self.conn,
            id,
            scan_id,
            package_name,
            drv_path,
            parent_id=parent_id,
            child_id=child_id,
            vulnerability_event_id=vulnerability_event_id,
            version=version,
            lineage=lineage,
        )
