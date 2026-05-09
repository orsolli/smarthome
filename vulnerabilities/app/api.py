"""API endpoints for the vulnerability frontend.

Provides HTMX-compatible endpoints for:
- /api/scans: List of scans for sidebar
- /api/tree/<scan_id>: HTML dependency tree
- /api/vuln-map/<scan_id>: JSON vulnerability map
"""

from core import database
from app.templates import base_html, tree_html
from core.normalizer import _cvss_from_severity


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
    conn = _get_db()
    cursor = conn.execute(
        "SELECT id, timestamp, target FROM scans ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    scans = [dict(zip(columns, row)) for row in rows]
    conn.close()

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


def api_tree_endpoint(scan_id: int):
    """Get dependency tree as HTML for a scan."""
    with _get_db() as conn:
        nodes = database.get_dependency_tree_for_scan(conn, scan_id)

    if not nodes:
        return "<p>No tree data available for this scan.</p>"

    # Build parent->children mapping
    children_map: dict[str, list[dict]] = {}
    root_nodes: list[dict] = []
    for node in nodes:
        parent_id = node.get("parent_id")
        if parent_id is None:
            root_nodes.append(node)
        else:
            children_map.setdefault(str(parent_id), []).append(node)

    # Get vuln map for severity coloring
    vuln_map: dict[str, dict] = {}
    with _get_db() as conn:
        cursor = conn.execute(
            "SELECT drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
            (scan_id,),
        )
        for row in cursor.fetchall():
            vuln_map[row[0]] = {"severity": row[1]}

    def _severity_class(drv_path: str) -> tuple[str, str]:
        """Return (severity_class, severity_label) for a drv_path."""
        info = vuln_map.get(drv_path, {})
        sev = info.get("severity", "NONE")
        return f"sev-{sev}", sev

    def _render(node: dict) -> tuple[str, str]:
        pname = node.get("package_name", "unknown")
        drv_path = node.get("drv_path", "")
        node_id = f"node-{drv_path.replace('/', '_').replace('.', '_')}"
        sev_class, severity = _severity_class(drv_path)
        children = children_map.get(str(node.get("id")), [])
        children_html = ""
        for child in children:
            html, child_severity = _render(child)
            children_html += html
            if _cvss_from_severity(child_severity) > _cvss_from_severity(severity):
                severity = child_severity
                sev_class = f"sev-{severity}"
        has_children = len(children_html) > 0

        html = f'<div class="tree-node" id="{node_id}">\n'
        html += f'  <div class="tree-node-header" onclick="toggleNode(\'{node_id}\')">\n'
        expand_class = "" if has_children else "leaf"
        html += f'    <span class="expand-icon {expand_class}">&#9654;</span>\n'
        html += f'    <span class="severity-dot {sev_class}"></span>\n'
        html += f'    <span class="pkg-name">{pname}</span>\n'
        html += f'    <span class="sev-label">{severity}</span>\n'
        html += f'  </div>\n'
        if has_children:
            html += f'  <div class="tree-children" id="{node_id}-children">\n'
            html += children_html
            html += "  </div>\n"
        html += "</div>"
        return html, severity

    result = ""
    for root in root_nodes:
        html, _severity = _render(root)
        result += html
    return result


def api_vuln_map_endpoint(scan_id: int):
    """Get vulnerability map as JSON for a scan."""
    conn = _get_db()
    cursor = conn.execute(
        "SELECT package_name, drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
        (scan_id,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    events = [dict(zip(columns, row)) for row in rows]
    conn.close()

    vuln_map: dict[str, dict] = {}
    for event in events:
        vuln_map[event["drv_path"]] = {
            "package_name": event["package_name"],
            "severity": event["severity"],
        }
    return vuln_map


def scan_detail_endpoint(scan_id: int):
    """Render scan detail page with tree and timeseries."""
    conn = _get_db()
    cursor = conn.execute(
        "SELECT id, timestamp, target FROM scans WHERE id = ?", (scan_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "<h1>Scan not found</h1>"
    columns = [desc[0] for desc in cursor.description]
    scan = dict(zip(columns, row))

    body = tree_html(scan_id, {})
    return base_html(f"Scan: {scan['target']}", body)
