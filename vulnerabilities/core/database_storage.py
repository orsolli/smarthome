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

    def insert_scan(self, target: str) -> int:
        """Insert a scan record and return its ID.

        Args:
            target: The derivation path scanned.

        Returns:
            The ID of the inserted scan.
        """
        return database.insert_scan(self.conn, target)

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
        return database.insert_vulnerability_event(
            self.conn, scan_id, package_name, drv_path, severity
        )

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
        return database.insert_dependency_node(
            self.conn,
            scan_id,
            package_name,
            drv_path,
            parent_id=parent_id,
            child_id=child_id,
            vulnerability_event_id=vulnerability_event_id,
        )
