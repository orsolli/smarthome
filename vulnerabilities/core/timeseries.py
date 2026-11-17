"""Timeseries queries for vulnerability visualization.

Provides functions to aggregate vulnerability events over time
for chart rendering.

Cross-scan timelines are keyed by node identity rather than derivation path:
a store hash changes on every rebuild, so `drv_path` never matches a node from
an older scan. See core/identity.py for how a node is recognised in another
scan of the same target.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Any


def _parse_iso(ts: str) -> datetime:
    """Parse an ISO timestamp, falling back to datetime.min."""
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return datetime.min


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


SEVERITY_RANK: dict[str, int] = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

RANK_SEVERITY: dict[int, str] = {rank: name for name, rank in SEVERITY_RANK.items()}


def _nodes_of_scan(conn: sqlite3.Connection, scan_id: int) -> list[dict[str, Any]]:
    """Fetch one scan's dependency tree nodes."""
    cursor = conn.execute(
        """SELECT id, package_name, version, lineage, drv_path, parent_id
           FROM dependency_tree WHERE scan_id = ?""",
        (scan_id,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def _subtree_severities(
    nodes: list[dict[str, Any]],
    event_severity: dict[str, str],
) -> dict[int, str]:
    """Aggregated severity per node: a node is as red as its worst descendant."""
    ids = {node["id"] for node in nodes}
    children: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        parent = node.get("parent_id")
        if parent is not None and parent in ids:
            children.setdefault(parent, []).append(node)

    severity: dict[int, str] = {}
    for root in nodes:
        if root["id"] in severity:
            continue
        stack: list[tuple[dict[str, Any], bool]] = [(root, False)]
        while stack:
            node, expanded = stack.pop()
            if node["id"] in severity:
                continue
            if not expanded:
                stack.append((node, True))
                for child in children.get(node["id"], []):
                    if child["id"] not in severity:
                        stack.append((child, False))
                continue
            worst = event_severity.get(node.get("drv_path", ""), "NONE")
            for child in children.get(node["id"], []):
                child_severity = severity.get(child["id"], "NONE")
                if SEVERITY_RANK.get(child_severity, 0) > SEVERITY_RANK.get(worst, 0):
                    worst = child_severity
            severity[node["id"]] = worst
    return severity


def _common_prefix_len(left: str, right: str) -> int:
    """Number of leading lineage segments two lineages share."""
    left_parts = left.split("/")
    right_parts = right.split("/")
    count = 0
    while count < len(left_parts) and count < len(right_parts) and left_parts[count] == right_parts[count]:
        count += 1
    return count


def _scan_index(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build lookup tables used to find a node in another scan."""
    by_lineage: dict[str, list[dict[str, Any]]] = {}
    by_name: dict[str, list[dict[str, Any]]] = {}
    name_counts: dict[str, int] = {}
    for node in nodes:
        lineage = node.get("lineage")
        if lineage:
            by_lineage.setdefault(lineage, []).append(node)
        by_name.setdefault(node["package_name"], []).append(node)
        name_counts[node["package_name"]] = name_counts.get(node["package_name"], 0) + 1
    return {"by_lineage": by_lineage, "by_name": by_name, "name_counts": name_counts}


def _pick(candidates: list[dict[str, Any]], node: dict[str, Any]) -> dict[str, Any]:
    """Deterministically choose among equally qualified counterpart nodes."""
    lineage = node.get("lineage") or ""
    return max(
        candidates,
        key=lambda c: (_common_prefix_len(lineage, c.get("lineage") or ""), c["id"]),
    )


def _find_counterpart(
    node: dict[str, Any],
    index: dict[str, Any],
    own_name_count: int,
) -> dict[str, Any] | None:
    """Find the node representing the same package in another scan of the target.

    Falls through, from the most specific to the most general:
        1. same lineage and version
        2. same lineage, different version (the package was upgraded)
        3. same name and version elsewhere in the tree (it moved)
        4. same name, when that name is unique in both trees
        5. otherwise the node is new in this scan and has no history
    """
    name = node["package_name"]
    version = node.get("version") or ""
    lineage = node.get("lineage")

    if lineage:
        lineage_nodes = index["by_lineage"].get(lineage, [])
        exact = [c for c in lineage_nodes if (c.get("version") or "") == version]
        if exact:
            return _pick(exact, node)
        if lineage_nodes:
            return _pick(lineage_nodes, node)

    if version:
        moved = [
            c for c in index["by_name"].get(name, []) if (c.get("version") or "") == version
        ]
        if moved:
            return _pick(moved, node)

    if own_name_count == 1 and index["name_counts"].get(name, 0) == 1:
        return index["by_name"][name][0]

    return None


def get_tree_subtree_timelines(
    conn: sqlite3.Connection,
    scan_id: int,
) -> dict[str, list[dict[str, Any]]]:
    """Get subtree-aggregated timelines for every node of a scan's tree.

    Every scan sharing the target of `scan_id` is inspected, and each node is
    matched to its counterpart in those scans by identity (name, version and
    compressed lineage) instead of by derivation path. The value recorded for a
    scan is the highest severity found anywhere in that node's subtree, so a
    child being red makes the parent red.

    Args:
        conn: Database connection.
        scan_id: Scan whose dependency tree defines the structure.

    Returns:
        Dict mapping drv_path -> list of dicts with keys:
        scan_id, timestamp, severity, version, ordered by timestamp. A scan
        where the node existed but was clean appears with severity NONE, which
        is what makes a fixed vulnerability end the bar.
    """
    nodes = _nodes_of_scan(conn, scan_id)
    if not nodes:
        return {}

    target_scans = [
        (scan_id_row, timestamp)
        for scan_id_row, timestamp in conn.execute(
            """SELECT s.id, s.timestamp
               FROM scans s
               WHERE s.target = (SELECT target FROM scans WHERE id = ?)
               ORDER BY s.timestamp""",
            (scan_id,),
        ).fetchall()
    ]

    scan_data: dict[int, dict[str, Any]] = {}
    for other_id, timestamp in target_scans:
        other_nodes = _nodes_of_scan(conn, other_id)
        if not other_nodes:
            continue
        severities = {
            drv_path: severity
            for drv_path, severity in conn.execute(
                "SELECT drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
                (other_id,),
            ).fetchall()
        }
        scan_data[other_id] = {
            "timestamp": timestamp,
            "index": _scan_index(other_nodes),
            "severity": _subtree_severities(other_nodes, severities),
        }

    own_name_counts: dict[str, int] = {}
    for node in nodes:
        own_name_counts[node["package_name"]] = own_name_counts.get(node["package_name"], 0) + 1

    timelines: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        entries: list[dict[str, Any]] = []
        for other_id, _ in target_scans:
            data = scan_data.get(other_id)
            if data is None:
                continue
            counterpart = _find_counterpart(node, data["index"], own_name_counts[node["package_name"]])
            if counterpart is None:
                continue
            entries.append({
                "scan_id": other_id,
                "timestamp": data["timestamp"],
                "severity": data["severity"].get(counterpart["id"], "NONE"),
                "version": counterpart.get("version") or "",
            })
        timelines[node["drv_path"]] = entries

    return timelines


def get_subtree_timeseries(
    conn: sqlite3.Connection,
    scan_id: int,
    drv_path: str,
) -> list[dict[str, Any]]:
    """Get the timeline of the subtree rooted at drv_path.

    Convenience wrapper around get_tree_subtree_timelines for a single node.

    Args:
        conn: Database connection.
        scan_id: Scan whose dependency tree defines the subtree.
        drv_path: Derivation path of the subtree root node.

    Returns:
        List of dicts with keys: scan_id, timestamp, severity, version.
    """
    return get_tree_subtree_timelines(conn, scan_id).get(drv_path, [])


def get_scan_window(
    conn: sqlite3.Connection,
    pad_days: int = 1,
) -> tuple[datetime, datetime]:
    """Earliest and latest scan timestamps, padded for chart rendering.

    Args:
        conn: Database connection.
        pad_days: Days to add on each side of the window.

    Returns:
        (start, end) datetime pair covering every scan.
    """
    cursor = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM scans")
    lowest, highest = cursor.fetchone()
    if lowest is None or highest is None:
        return datetime.min, datetime.max
    return _parse_iso(lowest) - timedelta(days=pad_days), _parse_iso(highest) + timedelta(days=pad_days)


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
