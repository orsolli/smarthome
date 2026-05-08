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
