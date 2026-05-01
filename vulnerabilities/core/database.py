"""Database schema and initialization for vulnerability tracking.

Tables:
    scans: Scan metadata (timestamp, target, etc.)
    vulnerability_events: Time-series vulnerability records
    dependency_tree: Structural dependency mapping per scan
"""

import sqlite3
from datetime import datetime
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    target TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vulnerability_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    package_name TEXT NOT NULL,
    drv_path TEXT NOT NULL,
    severity TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scans(id)
);

CREATE TABLE IF NOT EXISTS dependency_tree (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    vulnerability_event_id INTEGER,
    package_name TEXT NOT NULL,
    drv_path TEXT NOT NULL,
    parent_id INTEGER,
    child_id INTEGER,
    FOREIGN KEY (scan_id) REFERENCES scans(id),
    FOREIGN KEY (parent_id) REFERENCES dependency_tree(id),
    FOREIGN KEY (child_id) REFERENCES dependency_tree(id),
    FOREIGN KEY (vulnerability_event_id) REFERENCES vulnerability_events(id)
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database and return a connection.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection with schema initialized.
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def insert_scan(conn: sqlite3.Connection, target: str) -> int:
    """Insert a scan record and return its ID.

    Args:
        conn: Database connection.
        target: The derivation path scanned.

    Returns:
        The ID of the inserted scan.
    """
    cursor = conn.execute(
        "INSERT INTO scans (timestamp, target) VALUES (?, ?)",
        (datetime.utcnow().isoformat(), target),
    )
    conn.commit()
    return cursor.lastrowid or 0


def insert_vulnerability_event(
    conn: sqlite3.Connection,
    scan_id: int,
    package_name: str,
    drv_path: str,
    severity: str,
) -> int:
    """Insert a vulnerability event and return its ID.

    Args:
        conn: Database connection.
        scan_id: Linking scan ID.
        package_name: Package name (e.g. 'Diff').
        drv_path: Nix derivation path.
        severity: Severity level (e.g. 'CRITICAL').

    Returns:
        The ID of the inserted event.
    """
    cursor = conn.execute(
        "INSERT INTO vulnerability_events (scan_id, package_name, drv_path, severity, timestamp) VALUES (?, ?, ?, ?, ?)",
        (scan_id, package_name, drv_path, severity, datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cursor.lastrowid or 0


def insert_dependency_node(
    conn: sqlite3.Connection,
    scan_id: int,
    package_name: str,
    drv_path: str,
    parent_id: int | None = None,
    child_id: int | None = None,
    vulnerability_event_id: int | None = None,
) -> int:
    """Insert a dependency tree node and return its ID.

    Args:
        conn: Database connection.
        scan_id: Linking scan ID.
        package_name: Package name.
        drv_path: Nix derivation path.
        parent_id: Optional parent node ID.
        child_id: Optional child node ID.
        vulnerability_event_id: Optional linked vulnerability event ID.

    Returns:
        The ID of the inserted node.
    """
    cursor = conn.execute(
        """INSERT INTO dependency_tree
           (scan_id, package_name, drv_path, parent_id, child_id, vulnerability_event_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (scan_id, package_name, drv_path, parent_id, child_id, vulnerability_event_id),
    )
    conn.commit()
    return cursor.lastrowid or 0


def get_vulnerabilities_since(
    conn: sqlite3.Connection, since: str, until: str | None = None
) -> list[dict[str, Any]]:
    """Query vulnerability events within a time range.

    Args:
        conn: Database connection.
        since: Start timestamp (ISO format).
        until: Optional end timestamp (ISO format).

    Returns:
        List of vulnerability event dicts.
    """
    if until:
        cursor = conn.execute(
            """SELECT v.id, v.package_name, v.drv_path, v.severity,
                      s.timestamp, s.target
               FROM vulnerability_events v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.timestamp >= ? AND s.timestamp <= ?
               ORDER BY s.timestamp""",
            (since, until),
        )
    else:
        cursor = conn.execute(
            """SELECT v.id, v.package_name, v.drv_path, v.severity,
                      s.timestamp, s.target
               FROM vulnerability_events v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.timestamp >= ?
               ORDER BY s.timestamp""",
            (since,),
        )

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_dependency_tree_for_scan(conn: sqlite3.Connection, scan_id: int) -> list[dict[str, Any]]:
    """Get the dependency tree for a specific scan.

    Args:
        conn: Database connection.
        scan_id: The scan ID.

    Returns:
        List of dependency tree nodes.
    """
    cursor = conn.execute(
        """SELECT id, scan_id, vulnerability_event_id, package_name, drv_path, parent_id, child_id
           FROM dependency_tree
           WHERE scan_id = ?""",
        (scan_id,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
