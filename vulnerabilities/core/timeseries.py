"""Timeseries queries for vulnerability visualization.

Provides functions to aggregate vulnerability events over time
for chart rendering.
"""

import sqlite3
from typing import Any


def get_timeseries_for_package(
    conn: sqlite3.Connection,
    package_name: str,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]]:
    """Get vulnerability timeline for a single package.

    Returns one row per scan where the package was vulnerable.

    Args:
        conn: Database connection.
        package_name: Package to query.
        since: Optional start timestamp.
        until: Optional end timestamp.

    Returns:
        List of dicts with keys: scan_id, timestamp, severity, target.
    """
    base = """
        SELECT v.scan_id, v.package_name, s.timestamp, v.severity, s.target
        FROM vulnerability_events v
        JOIN scans s ON v.scan_id = s.id
        WHERE v.package_name = ?
    """
    params: list[Any] = [package_name]

    if since:
        base += " AND s.timestamp >= ?"
        params.append(since)
    if until:
        base += " AND s.timestamp <= ?"
        params.append(until)

    base += " ORDER BY s.timestamp"

    cursor = conn.execute(base, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_timeseries_for_all_packages(
    conn: sqlite3.Connection,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]]:
    """Get vulnerability timeline for all packages.

    Returns one row per (scan_id, package_name, severity) combination.

    Args:
        conn: Database connection.
        since: Optional start timestamp.
        until: Optional end timestamp.

    Returns:
        List of dicts with keys: scan_id, timestamp, package_name, severity, target.
    """
    base = """
        SELECT v.scan_id, v.package_name, s.timestamp, v.severity, s.target
        FROM vulnerability_events v
        JOIN scans s ON v.scan_id = s.id
    """
    params: list[Any] = []

    if since:
        base += " WHERE s.timestamp >= ?"
        params.append(since)
    if until:
        base += " AND s.timestamp <= ?"
        params.append(until)

    base += " ORDER BY s.timestamp, v.package_name"

    cursor = conn.execute(base, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def get_subtree_timeseries(
    conn: sqlite3.Connection,
    scan_id: int,
    drv_path: str,
) -> list[dict[str, Any]]:
    """Get vulnerability timeline for the subtree rooted at drv_path.

    The subtree structure is taken from the dependency tree of `scan_id`;
    the timeline aggregates vulnerability events for every package in
    that subtree across *all* scans, yielding one row per scan with the
    highest severity found in the subtree (a child being red makes the
    parent red).

    Args:
        conn: Database connection.
        scan_id: Scan whose dependency tree defines the subtree.
        drv_path: Derivation path of the subtree root node.

    Returns:
        List of dicts with keys: scan_id, timestamp, severity.
    """
    cursor = conn.execute(
        """
        WITH RECURSIVE subtree(id, package_name) AS (
            SELECT id, package_name
            FROM dependency_tree
            WHERE drv_path = ? AND scan_id = ?
            UNION ALL
            SELECT dt.id, dt.package_name
            FROM dependency_tree dt
            JOIN subtree s ON dt.parent_id = s.id
        )
        SELECT v.scan_id, s.timestamp, v.severity
        FROM vulnerability_events v
        JOIN scans s ON v.scan_id = s.id
        WHERE v.package_name IN (SELECT package_name FROM subtree)
        ORDER BY s.timestamp
        """,
        (drv_path, scan_id),
    )

    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
    by_scan: dict[int, dict[str, Any]] = {}
    for event_scan_id, timestamp, severity in cursor.fetchall():
        entry = by_scan.get(event_scan_id)
        if entry is None:
            by_scan[event_scan_id] = {
                "scan_id": event_scan_id,
                "timestamp": timestamp,
                "severity": severity,
            }
        elif severity_order.get(severity, 0) > severity_order.get(entry["severity"], 0):
            entry["severity"] = severity

    return sorted(by_scan.values(), key=lambda e: e["timestamp"])


def get_aggregated_severity(
    conn: sqlite3.Connection,
    scan_id: int,
    package_name: str,
) -> dict[str, Any]:
    """Get aggregated severity for a package across scans.

    Returns max severity and count of scans where vulnerable.

    Args:
        conn: Database connection.
        scan_id: Scan to aggregate within.
        package_name: Package name.

    Returns:
        Dict with keys: max_severity, scan_count, latest_severity.
    """
    cursor = conn.execute(
        """
        SELECT v.severity, COUNT(*) as cnt
        FROM vulnerability_events v
        JOIN scans s ON v.scan_id = s.id
        WHERE v.package_name = ? AND s.id = ?
        GROUP BY v.severity
        ORDER BY cnt DESC
        """,
        (package_name, scan_id),
    )
    rows = cursor.fetchall()
    severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_sev = "LOW"
    max_score = 0
    total = 0
    latest_sev = "LOW"
    for row in rows:
        sev, cnt = row
        total += cnt
        score = severity_order.get(sev, 0)
        if score > max_score:
            max_score = score
            max_sev = sev
        latest_sev = sev  # last group wins (arbitrary, just pick one)
    return {
        "max_severity": max_sev,
        "scan_count": total,
        "latest_severity": latest_sev,
    }
