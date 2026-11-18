"""API endpoints for the vulnerability frontend.

Provides HTMX-compatible endpoints for:
- /api/scans: List of scans for sidebar
- /api/tree/<scan_id>: HTML dependency tree
- /api/bars/<scan_id>: timeline bars for the roots and their children
- /api/bars/<scan_id>/<drv_path>: timeline bars for a node's children
- /api/children/<scan_id>/<drv_path>: children beyond the visible limit
- /api/vuln-map/<scan_id>: JSON vulnerability map
"""

from contextlib import closing
from datetime import datetime

from app.chart import mini_bar_html
from app.colors import severity_rank
from app.templates import base_html, tree_html
from core import database, timeseries


def _get_db():
    """Get database connection from app context."""
    import os
    from pathlib import Path
    db_path = os.environ.get(
        "DATABASE_PATH",
        str(Path.home() / ".local" / "share" / "vulnerabilities" / "vulnerabilities.db"),
    )
    return database.init_db(db_path)


def api_scans_endpoint():
    """Get list of scans for sidebar (HTMX)."""
    with closing(_get_db()) as conn:
        cursor = conn.execute(
            "SELECT id, timestamp, target FROM scans ORDER BY timestamp DESC"
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        scans = [dict(zip(columns, row)) for row in rows]

    html = ""
    for s in scans:
        html += (
            f'<div class="scan-item" '
            f'hx-get="/scan/{s["id"]}" '
            f'hx-swap="innerHTML" '
            f'hx-trigger="click" '
            f'hx-target="#detail-panel">'
            f'{s["target"]} ({s["timestamp"]})</div>'
        )
    return html


MAX_VISIBLE_CHILDREN = 50


def _node_id(drv_path: str) -> str:
    """DOM id for a tree node."""
    return f"node-{drv_path.replace('/', '_').replace('.', '_')}"


def _children_map(nodes: list[dict]) -> dict[str, list[dict]]:
    """Map parent node id -> list of child nodes."""
    children: dict[str, list[dict]] = {}
    for node in nodes:
        parent_id = node.get("parent_id")
        if parent_id is not None:
            children.setdefault(str(parent_id), []).append(node)
    return children


def _vuln_map(conn, scan_id: int) -> dict[str, dict]:
    """drv_path -> {"severity": ...} for a scan's vulnerability events."""
    cursor = conn.execute(
        "SELECT drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
        (scan_id,),
    )
    return {row[0]: {"severity": row[1]} for row in cursor.fetchall()}


def _subtree_severities(
    nodes: list[dict],
    vuln_map: dict[str, dict],
) -> dict[str, str]:
    """Aggregated severity per node: a node is as red as its worst descendant."""
    severities = timeseries.subtree_severities(
        nodes, {drv_path: info["severity"] for drv_path, info in vuln_map.items()}
    )
    return {str(node_id): severity for node_id, severity in severities.items()}


def _ordered_children(
    node: dict,
    children_map: dict[str, list[dict]],
    severity: dict[str, str],
) -> list[dict]:
    """Children sorted by aggregated severity (worst first), then name."""
    return sorted(
        children_map.get(str(node["id"]), []),
        key=lambda c: (
            -severity_rank(severity.get(str(c["id"]), "NONE")),
            c.get("package_name", ""),
        ),
    )


def _render_node(
    node: dict,
    children_map: dict[str, list[dict]],
    severity: dict[str, str],
    scan_id: int,
    offset: int = 0,
) -> str:
    """Render one tree node, its empty timeline slot, and its children.

    Nodes with more than MAX_VISIBLE_CHILDREN children are truncated and
    get a "show more" button that loads the rest lazily.

    Args:
        node: Tree node dict.
        children_map: Parent id -> child nodes.
        severity: Aggregated severity per node id.
        scan_id: Scan the tree belongs to.
        offset: Number of children to skip (for the "show more" response).

    Returns:
        HTML string for the node.
    """
    node_id = _node_id(node["drv_path"])
    drv_path = node["drv_path"]
    sev = severity.get(str(node["id"]), "NONE")
    children = _ordered_children(node, children_map, severity)
    has_children = bool(children)

    html = f'<div class="tree-node" id="{node_id}">\n'
    if has_children:
        html += f'  <div class="tree-node-header" onclick="toggleNode(\'{node_id}\')">\n'
    else:
        html += '  <div class="tree-node-header">\n'
    html += f'    <span class="expand-icon {"leaf" if not has_children else ""}">&#9654;</span>\n'
    html += f'    <span class="severity-dot sev-{sev}"></span>\n'
    html += f'    <span class="pkg-name">{node.get("package_name", "unknown")}</span>\n'
    html += f'    <span class="sev-label">{sev}</span>\n'
    html += '  </div>\n'
    html += f'  <div class="node-timeline" id="{node_id}-timeline"></div>\n'

    if has_children:
        html += f'  <div class="tree-children" id="{node_id}-children"\n'
        html += f'    hx-get="/api/bars/{scan_id}/{drv_path}"\n'
        html += f'    hx-trigger="node-expanded"\n'
        html += f'    hx-swap="none">\n'
        for child in children[offset:offset + MAX_VISIBLE_CHILDREN]:
            html += _render_node(child, children_map, severity, scan_id)
        remaining = len(children) - offset - MAX_VISIBLE_CHILDREN
        if remaining > 0:
            html += (
                f'    <button class="show-more" '
                f'hx-get="/api/children/{scan_id}/{drv_path}?offset={offset + MAX_VISIBLE_CHILDREN}" '
                f'hx-target="#{node_id}-children" hx-swap="beforeend" '
                f'hx-trigger="click">show {remaining} more children</button>\n'
            )
        html += "  </div>\n"

    html += "</div>"
    return html


def api_tree_endpoint(scan_id: int):
    """Get dependency tree as HTML for a scan."""
    with closing(_get_db()) as conn:
        nodes = database.get_dependency_tree_for_scan(conn, scan_id)
        vuln_map = _vuln_map(conn, scan_id)

    if not nodes:
        return "<p>No tree data available for this scan.</p>"

    children_map = _children_map(nodes)
    severity = _subtree_severities(nodes, vuln_map)

    root_nodes = [n for n in nodes if n.get("parent_id") is None]
    result = ""
    for root in sorted(
        root_nodes,
        key=lambda n: (-severity_rank(severity.get(str(n["id"]), "NONE")), n["drv_path"]),
    ):
        result += _render_node(root, children_map, severity, scan_id)

    # Fill the roots' and their children's bars once the tree is in the DOM
    result += (
        f'<div id="bars-bootstrap" hx-get="/api/bars/{scan_id}" '
        'hx-trigger="load" hx-swap="none"></div>'
    )
    return result


def api_vuln_map_endpoint(scan_id: int):
    """Get vulnerability map as JSON for a scan."""
    with closing(_get_db()) as conn:
        cursor = conn.execute(
            "SELECT package_name, drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
            (scan_id,),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        events = [dict(zip(columns, row)) for row in rows]

    vuln_map: dict[str, dict] = {}
    for event in events:
        vuln_map[event["drv_path"]] = {
            "package_name": event["package_name"],
            "severity": event["severity"],
        }
    return vuln_map


def _bars_html(
    nodes: list[dict],
    timelines: dict[str, list[dict]],
    start: datetime,
    end: datetime,
) -> str:
    """Out-of-band HTML filling the timeline slot of each given node."""
    html = ""
    for node in nodes:
        html += (
            f'<div id="{_node_id(node["drv_path"])}-timeline" class="node-timeline" '
            'hx-swap-oob="true">'
            f'{mini_bar_html(timelines.get(node["drv_path"], []), start, end)}'
            f"</div>"
        )
    return html


def api_bars_endpoint(scan_id: int, drv_path: str | None = None) -> str:
    """HTMX out-of-band bars for a node's children (roots on tree load).

    Args:
        scan_id: Scan whose dependency tree defines the structure.
        drv_path: Derivation path of the expanded node. Omit for the
            bootstrap request, which fills the roots and their children.
            The HTMX URL embeds it without its leading slash, since
            Bottle consumes the separator slash between route segments.

    Returns:
        HTML string of out-of-band timeline divs.
    """
    with closing(_get_db()) as conn:
        nodes = database.get_dependency_tree_for_scan(conn, scan_id)
        if not nodes:
            return ""
        children_map = _children_map(nodes)
        severity = _subtree_severities(nodes, _vuln_map(conn, scan_id))
        start, end = timeseries.get_scan_window(conn, scan_id)
        timelines = timeseries.get_tree_subtree_timelines(conn, scan_id)

    if drv_path is None:
        roots = [n for n in nodes if n.get("parent_id") is None]
        targets = list(roots)
        for root in roots:
            targets.extend(_ordered_children(root, children_map, severity)[:MAX_VISIBLE_CHILDREN])
    else:
        if not drv_path.startswith("/"):
            drv_path = "/" + drv_path
        parent = next((n for n in nodes if n["drv_path"] == drv_path), None)
        if parent is None:
            return ""
        targets = _ordered_children(parent, children_map, severity)

    return _bars_html(targets, timelines, start, end)


def api_children_endpoint(
    scan_id: int,
    drv_path: str,
    offset: int = MAX_VISIBLE_CHILDREN,
) -> str:
    """HTMX response: children of a node beyond the visible limit, with bars.

    Args:
        scan_id: Scan whose dependency tree defines the structure.
        drv_path: Derivation path of the node whose children are requested.
        offset: Number of already-rendered children to skip.

    Returns:
        HTML string: the remaining tree nodes plus their timeline bars.
    """
    if not drv_path.startswith("/"):
        drv_path = "/" + drv_path

    with closing(_get_db()) as conn:
        nodes = database.get_dependency_tree_for_scan(conn, scan_id)
        if not nodes:
            return ""
        children_map = _children_map(nodes)
        severity = _subtree_severities(nodes, _vuln_map(conn, scan_id))
        start, end = timeseries.get_scan_window(conn, scan_id)
        timelines = timeseries.get_tree_subtree_timelines(conn, scan_id)

    parent = next((n for n in nodes if n["drv_path"] == drv_path), None)
    if parent is None:
        return ""

    hidden = _ordered_children(parent, children_map, severity)[offset:]
    html = "".join(
        _render_node(child, children_map, severity, scan_id) for child in hidden
    )
    return html + _bars_html(hidden, timelines, start, end)


def scan_detail_endpoint(scan_id: int):
    """Render scan detail page: dependency tree with inline timelines."""
    with closing(_get_db()) as conn:
        cursor = conn.execute(
            "SELECT id, timestamp, target FROM scans WHERE id = ?", (scan_id,)
        )
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]

    if not row:
        return "<h1>Scan not found</h1>"
    scan = dict(zip(columns, row))

    return base_html(f"Scan: {scan['target']}", tree_html(scan_id))
