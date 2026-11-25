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

from core.severity import aggregate_severity, severity_rank


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
    return [dict(row) for row in cursor.fetchall()]


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
    return [dict(row) for row in cursor.fetchall()]


def _nodes_of_scan(conn: sqlite3.Connection, scan_id: int) -> list[dict[str, Any]]:
    """Fetch one scan's dependency tree nodes."""
    cursor = conn.execute(
        """SELECT id, package_name, version, lineage, drv_path, parent_id
           FROM dependency_tree WHERE scan_id = ?""",
        (scan_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _label(node: dict[str, Any]) -> str:
    """Readable "name version" for a node, with the version optional."""
    version = node.get("version") or ""
    name = node.get("package_name", "")
    return f"{name} {version}".strip()


def subtree_worst(
    nodes: list[dict[str, Any]],
    event_severity: dict[str, str],
) -> dict[int, tuple[str, str]]:
    """Aggregated severity per node, and the descendant that drives it.

    A node is as red as its worst descendant. The second element of the pair is
    the "name version" of the nearest node in that subtree whose own event has
    the aggregated severity, or "" when the node's own event is the driver. A
    clean node gets ("NONE", "").

    Args:
        nodes: Nodes of one scan's dependency tree.
        event_severity: drv_path -> severity of that node's own event.

    Returns:
        Dict mapping node id -> (aggregated severity, driving descendant label).
    """
    ids = {node["id"] for node in nodes}
    children: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        parent = node.get("parent_id")
        if parent is not None and parent in ids:
            children.setdefault(parent, []).append(node)

    worst: dict[int, tuple[str, str]] = {}
    for root in nodes:
        if root["id"] in worst:
            continue
        stack: list[tuple[dict[str, Any], bool]] = [(root, False)]
        while stack:
            node, expanded = stack.pop()
            if node["id"] in worst:
                continue
            if not expanded:
                stack.append((node, True))
                for child in children.get(node["id"], []):
                    if child["id"] not in worst:
                        stack.append((child, False))
                continue
            severity = event_severity.get(node.get("drv_path", ""), "NONE")
            driver = ""
            for child in children.get(node["id"], []):
                child_severity, child_driver = worst.get(child["id"], ("NONE", ""))
                if severity_rank(child_severity) > severity_rank(severity):
                    severity = child_severity
                    driver = child_driver or _label(child)
            worst[node["id"]] = (severity, driver)
    return worst


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
    since: datetime | str | None = None,
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
        since: Optional cutoff. Scans before it are not bar boundaries, which
            is what makes a bar zoom into a recent window.

    Returns:
        Dict mapping drv_path -> list of dicts with keys:
        scan_id, timestamp, severity, name, version, source, ordered by
        timestamp. `name` is the node's own package name, `version` the version
        its counterpart had in that scan, and `source` the descendant driving
        that scan's severity, or "" when the node itself is the cause. A scan
        where the node existed but was clean appears with severity NONE, which
        is what makes a fixed vulnerability end the bar.
    """
    nodes = _nodes_of_scan(conn, scan_id)
    if not nodes:
        return {}

    cutoff = since.isoformat() if isinstance(since, datetime) else since
    query = """SELECT s.id, s.timestamp
               FROM scans s
               WHERE s.target = (SELECT target FROM scans WHERE id = ?)"""
    params: list[Any] = [scan_id]
    if cutoff is not None:
        query += " AND s.timestamp >= ?"
        params.append(cutoff)
    target_scans = conn.execute(query + " ORDER BY s.timestamp", params).fetchall()

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
            "worst": subtree_worst(other_nodes, severities),
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
            severity, driver = data["worst"].get(counterpart["id"], ("NONE", ""))
            entries.append({
                "scan_id": other_id,
                "timestamp": data["timestamp"],
                "severity": severity,
                "version": counterpart.get("version") or "",
                "name": node["package_name"],
                "source": driver,
            })
        timelines[node["drv_path"]] = entries

    return timelines


def get_zoom_window(
    conn: sqlite3.Connection,
    scan_id: int,
    days: int | None = None,
    pad_days: int = 1,
) -> tuple[str | None, datetime, datetime]:
    """Chart window for one target, zoomed to the last `days` days when given.

    The cutoff is `days` before the newest scan of the target, so it cannot be
    written as a SQL predicate: it depends on a value that query is computing.
    A target has few scans, so they are read in one query and cut here.

    Args:
        conn: Database connection.
        scan_id: Scan whose target defines the window.
        days: Length of the window in days, or None for the whole history.
        pad_days: Days to add on each side, so the first and last scan are not
            drawn as hairlines at the edges of a bar.

    Returns:
        (since, start, end): the ISO cutoff the timeline queries apply, None
        when the whole history is in scope, and the padded range bars are drawn
        in. A scan-less target gets an open-ended window.
    """
    timestamps = sorted(
        _parse_iso(row[0])
        for row in conn.execute(
            """SELECT timestamp FROM scans
               WHERE target = (SELECT target FROM scans WHERE id = ?)""",
            (scan_id,),
        )
    )
    if not timestamps:
        return None, datetime.min, datetime.max

    latest = timestamps[-1]
    since = latest - timedelta(days=days) if days else None
    in_window = [ts for ts in timestamps if since is None or ts >= since]
    return (
        since.isoformat() if since else None,
        in_window[0] - timedelta(days=pad_days),
        latest + timedelta(days=pad_days),
    )


def get_aggregated_severity(
    conn: sqlite3.Connection,
    scan_id: int,
    package_name: str,
) -> dict[str, Any]:
    """Get aggregated severity for a package within one scan.

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
        """,
        (package_name, scan_id),
    )
    rows = cursor.fetchall()
    if not rows:
        return {"max_severity": "NONE", "scan_count": 0, "latest_severity": "NONE"}

    severities = [severity for severity, _ in rows]
    latest = conn.execute(
        """SELECT severity FROM vulnerability_events
           WHERE package_name = ? AND scan_id = ?
           ORDER BY timestamp DESC LIMIT 1""",
        (package_name, scan_id),
    ).fetchone()[0]
    return {
        "max_severity": aggregate_severity(severities),
        "scan_count": sum(count for _, count in rows),
        "latest_severity": latest,
    }
