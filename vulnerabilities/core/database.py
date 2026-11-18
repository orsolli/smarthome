"""Database schema and initialization for vulnerability tracking.

Tables:
    scans: Scan metadata (timestamp, target)
    vulnerability_events: Time-series vulnerability records
    dependency_tree: Structural dependency mapping per scan

A node's identity across scans is carried by `package_name`, `version` and
`lineage` (see core/identity.py). `drv_path` contains a store hash that changes
with every rebuild, so it is only unique inside a single scan; the `target` of a
scan is what groups scans of the same machine or build together.
"""

import sqlite3
from datetime import datetime
from typing import Any

from core.identity import compressed_lineages, version_from_drv
from core.severity import aggregate_severity


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    target TEXT NOT NULL,
    scanned_path TEXT
);

CREATE TABLE IF NOT EXISTS vulnerability_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    package_name TEXT NOT NULL,
    version TEXT,
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
    version TEXT,
    lineage TEXT,
    drv_path TEXT NOT NULL,
    parent_id INTEGER,
    child_id INTEGER,
    FOREIGN KEY (scan_id) REFERENCES scans(id),
    FOREIGN KEY (parent_id) REFERENCES dependency_tree(id),
    FOREIGN KEY (child_id) REFERENCES dependency_tree(id),
    FOREIGN KEY (vulnerability_event_id) REFERENCES vulnerability_events(id)
);
"""

# Columns added to databases created before cross-scan node identity existed.
ADDED_COLUMNS: dict[str, dict[str, str]] = {
    "scans": {"scanned_path": "TEXT"},
    "vulnerability_events": {"version": "TEXT"},
    "dependency_tree": {"version": "TEXT", "lineage": "TEXT"},
}


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns that older databases are missing."""
    for table, columns in ADDED_COLUMNS.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column, definition in columns.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    conn.execute("CREATE INDEX IF NOT EXISTS idx_tree_scan ON dependency_tree(scan_id)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_tree_lineage ON dependency_tree(lineage)"
    )
    conn.commit()


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize the database and return a connection.

    Existing databases are migrated in place: the version and lineage columns
    are added when absent.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection with schema initialized.
    """
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    _migrate(conn)
    conn.commit()
    return conn


def insert_scan(
    conn: sqlite3.Connection,
    target: str,
    timestamp: str | None = None,
    scanned_path: str | None = None,
) -> int:
    """Insert a scan record and return its ID.

    Args:
        conn: Database connection.
        target: The identity of what was scanned. Scans of the same target
            share timeline history.
        timestamp: ISO timestamp of the scan. Defaults to now, but a
            backfill of an old Nix generation passes the date that
            generation was activated.
        scanned_path: The derivation path actually handed to vulnix. For a
            backfilled generation this is a profile link such as
            /nix/var/nix/profiles/system-3-link, while `target` stays
            /run/current-system. Defaults to the target.

    Returns:
        The ID of the inserted scan.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    if scanned_path is None:
        scanned_path = target
    cursor = conn.execute(
        "INSERT INTO scans (timestamp, target, scanned_path) VALUES (?, ?, ?)",
        (timestamp, target, scanned_path),
    )
    conn.commit()
    return cursor.lastrowid or 0


def insert_vulnerability_event(
    conn: sqlite3.Connection,
    scan_id: int,
    package_name: str,
    drv_path: str,
    severity: str,
    version: str | None = None,
    timestamp: str | None = None,
) -> int:
    """Insert a vulnerability event and return its ID.

    Args:
        conn: Database connection.
        scan_id: Linking scan ID.
        package_name: Package name (e.g. 'Diff').
        drv_path: Nix derivation path.
        severity: Severity level (e.g. 'CRITICAL').
        version: Version of the vulnerable derivation. Derived from drv_path
            when omitted.
        timestamp: When the scan that found it ran. Defaults to now. Events
            inherit the scan's timestamp so a backfilled generation does not
            look like it was found today.

    Returns:
        The ID of the inserted event.
    """
    if version is None:
        version = version_from_drv(drv_path, package_name)
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """INSERT INTO vulnerability_events
           (scan_id, package_name, version, drv_path, severity, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (scan_id, package_name, version, drv_path, severity, timestamp),
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
    version: str | None = None,
    lineage: str | None = None,
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
        version: Version of this derivation, used for cross-scan matching.
        lineage: Compressed lineage path, used for cross-scan matching.

    Returns:
        The ID of the inserted node.
    """
    if version is None:
        version = version_from_drv(drv_path, package_name)
    cursor = conn.execute(
        """INSERT INTO dependency_tree
           (scan_id, package_name, version, lineage, drv_path, parent_id,
            child_id, vulnerability_event_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            scan_id,
            package_name,
            version,
            lineage,
            drv_path,
            parent_id,
            child_id,
            vulnerability_event_id,
        ),
    )
    conn.commit()
    return cursor.lastrowid or 0


def update_dependency_node(
    conn: sqlite3.Connection,
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
    """Update a dependency tree node and return its ID.

    Args:
        conn: Database connection.
        id: The ID of the node to update.
        scan_id: Linking scan ID.
        package_name: Package name.
        drv_path: Nix derivation path.
        parent_id: Optional parent node ID.
        child_id: Optional child node ID.
        vulnerability_event_id: Optional linked vulnerability event ID.
        version: Version of this derivation.
        lineage: Compressed lineage path.

    Returns:
        The ID of the updated node.
    """
    existing = conn.execute(
        """SELECT scan_id, package_name, version, lineage, drv_path, parent_id,
                  child_id, vulnerability_event_id
           FROM dependency_tree WHERE id = ?""",
        (id,),
    ).fetchone()
    if not existing:
        raise ValueError(f"Node with ID {id} does not exist")

    scan_id = existing[0] if scan_id is None else scan_id
    package_name = existing[1] if package_name is None else package_name
    version = existing[2] if version is None else version
    lineage = existing[3] if lineage is None else lineage
    drv_path = existing[4] if drv_path is None else drv_path
    parent_id = existing[5] if parent_id is None else parent_id
    child_id = existing[6] if child_id is None else child_id
    vulnerability_event_id = (
        existing[7] if vulnerability_event_id is None else vulnerability_event_id
    )

    cursor = conn.execute(
        """UPDATE dependency_tree
           SET scan_id = ?, package_name = ?, version = ?, lineage = ?,
               drv_path = ?, parent_id = ?, child_id = ?, vulnerability_event_id = ?
           WHERE id = ?""",
        (
            scan_id,
            package_name,
            version,
            lineage,
            drv_path,
            parent_id,
            child_id,
            vulnerability_event_id,
            id,
        ),
    )
    conn.commit()
    return cursor.lastrowid or 0


def backfill_identities(conn: sqlite3.Connection) -> int:
    """Fill version and lineage for rows written before node identity existed.

    Idempotent: only rows with a NULL lineage or version are touched.

    Args:
        conn: Database connection.

    Returns:
        Number of scans whose tree was backfilled.
    """
    scan_ids = [
        row[0]
        for row in conn.execute(
            "SELECT DISTINCT scan_id FROM dependency_tree WHERE lineage IS NULL"
        ).fetchall()
    ]
    for scan_id in scan_ids:
        target = conn.execute(
            "SELECT target FROM scans WHERE id = ?", (scan_id,)
        ).fetchone()
        nodes = get_dependency_tree_for_scan(conn, scan_id)
        lineages = compressed_lineages(nodes, target[0] if target else "")
        for node in nodes:
            conn.execute(
                "UPDATE dependency_tree SET version = ?, lineage = ? WHERE id = ?",
                (
                    node["version"] or version_from_drv(node["drv_path"], node["package_name"]),
                    lineages[node["id"]],
                    node["id"],
                ),
            )
    conn.commit()

    for drv_path, package_name in conn.execute(
        "SELECT drv_path, package_name FROM vulnerability_events WHERE version IS NULL"
    ).fetchall():
        conn.execute(
            "UPDATE vulnerability_events SET version = ? WHERE drv_path = ? AND package_name = ?",
            (version_from_drv(drv_path, package_name), drv_path, package_name),
        )
    conn.commit()
    return len(scan_ids)


def get_scans_for_target(
    conn: sqlite3.Connection,
    scan_id: int,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Get every scan of the target the given scan belongs to, oldest first.

    Args:
        conn: Database connection.
        scan_id: Scan whose target to look up.
        since: Optional ISO timestamp; scans before it are left out, which is
            how the UI zooms a timeline into a recent window.

    Returns:
        List of dicts with keys: id, timestamp, target, scanned_path.
    """
    query = """SELECT id, timestamp, target, scanned_path
              FROM scans
              WHERE target = (SELECT target FROM scans WHERE id = ?)"""
    params: list[Any] = [scan_id]
    if since is not None:
        query += " AND timestamp >= ?"
        params.append(since)
    cursor = conn.execute(query + " ORDER BY timestamp", params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def list_targets(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """One row per scanned identity, most recently scanned first.

    A machine rebuilt eighteen times is one target with eighteen scans, so the
    unit worth listing is the identity rather than the individual scan.

    Args:
        conn: Database connection.

    Returns:
        List of dicts with keys: target, scan_count, first_scan, last_scan,
        latest_scan_id, worst_severity. `worst_severity` is the worst severity
        recorded in the latest scan of the target, i.e. its current status, not
        the worst it ever had.
    """
    cursor = conn.execute(
        """SELECT target,
                  COUNT(*) AS scan_count,
                  MIN(timestamp) AS first_scan,
                  MAX(timestamp) AS last_scan,
                  (SELECT id FROM scans s2
                   WHERE s2.target = s.target
                   ORDER BY s2.timestamp DESC, s2.id DESC
                   LIMIT 1) AS latest_scan_id
           FROM scans s
           GROUP BY target
           ORDER BY last_scan DESC"""
    )
    columns = [desc[0] for desc in cursor.description]
    targets = [dict(zip(columns, row)) for row in cursor.fetchall()]

    for target in targets:
        severities = [
            row[0]
            for row in conn.execute(
                "SELECT severity FROM vulnerability_events WHERE scan_id = ?",
                (target["latest_scan_id"],),
            )
        ]
        target["worst_severity"] = aggregate_severity(severities)

    return targets


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
            """SELECT v.id, v.package_name, v.version, v.drv_path, v.severity,
                      s.timestamp, s.target
               FROM vulnerability_events v
               JOIN scans s ON v.scan_id = s.id
               WHERE s.timestamp >= ? AND s.timestamp <= ?
               ORDER BY s.timestamp""",
            (since, until),
        )
    else:
        cursor = conn.execute(
            """SELECT v.id, v.package_name, v.version, v.drv_path, v.severity,
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
        """SELECT id, scan_id, vulnerability_event_id, package_name, version,
                  lineage, drv_path, parent_id, child_id
           FROM dependency_tree
           WHERE scan_id = ?""",
        (scan_id,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
