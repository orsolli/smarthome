"""HTML templates for the vulnerability frontend."""


def base_html(title: str, body: str) -> str:
    """Render the base HTML page.

    Args:
        title: Page title.
        body: Inner HTML content.

    Returns:
        Complete HTML string.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://unpkg.com/htmx.org@1.9.12"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; height: 100vh; }}
        #sidebar {{ width: 340px; background: #161b22; border-right: 1px solid #30363d; overflow-y: auto; padding: 16px; flex-shrink: 0; }}
        #main {{ flex: 1; overflow-y: auto; padding: 24px; }}
        h1 {{ font-size: 1.4rem; color: #58a6ff; margin-bottom: 16px; }}
        h2 {{ font-size: 1.1rem; color: #8b949e; margin-bottom: 12px; border-bottom: 1px solid #30363d; padding-bottom: 6px; }}
        .tree-node {{ margin-left: 20px; padding: 2px 0; }}
        .tree-node-header {{ cursor: pointer; display: flex; align-items: center; gap: 6px; padding: 3px 6px; border-radius: 4px; transition: background 0.15s; }}
        .tree-node-header:hover {{ background: #21262d; }}
        .tree-children {{ display: none; margin-left: 12px; border-left: 1px solid #30363d; }}
        .tree-children.expanded {{ display: block; }}
        .expand-icon {{ width: 14px; text-align: center; font-size: 0.8rem; color: #8b949e; transition: transform 0.15s; }}
        .expand-icon.expanded {{ transform: rotate(90deg); }}
        .expand-icon.leaf {{ visibility: hidden; }}
        .severity-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
        .sev-CRITICAL {{ background: #da3633; box-shadow: 0 0 6px #da363380; }}
        .sev-HIGH {{ background: #f0883e; box-shadow: 0 0 6px #f0883e80; }}
        .sev-MEDIUM {{ background: #d29922; box-shadow: 0 0 6px #d2992280; }}
        .sev-LOW {{ background: #3fb950; }}
        .sev-NONE {{ background: #30363d; }}
        .pkg-name {{ font-size: 0.85rem; }}
        .sev-label {{ font-size: 0.7rem; color: #8b949e; margin-left: auto; }}
        #chart-container {{ margin-top: 20px; }}
        .chart-bar {{ display: flex; align-items: center; margin: 2px 0; font-size: 0.75rem; }}
        .chart-bar-label {{ width: 100px; color: #8b949e; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .chart-bar-track {{ flex: 1; height: 16px; background: #21262d; border-radius: 3px; overflow: hidden; display: flex; }}
        .chart-bar-segment {{ height: 100%; transition: width 0.3s; }}
        .scan-list {{ margin: 8px 0; }}
        .scan-item {{ padding: 4px 8px; font-size: 0.8rem; color: #8b949e; cursor: pointer; border-radius: 4px; }}
        .scan-item:hover, .scan-item.active {{ background: #21262d; color: #58a6ff; }}
    </style>
</head>
<body>
    <div id="sidebar">
        {body}
    </div>
    <div id="main">
        <div id="detail-panel"></div>
    </div>
</body>
</html>"""


def home_content(scan_id: int | None = None) -> str:
    """Home page sidebar content.

    Args:
        scan_id: Optional selected scan ID.

    Returns:
        Sidebar HTML string.
    """
    return f"""<h1>Vulnerability Scanner</h1>
<h2>Scans</h2>
<div class="scan-list" id="scan-list"
     hx-get="/api/scans"
     hx-trigger="load"
     hx-swap="innerHTML">
</div>
<h2>Severity Legend</h2>
<div style="font-size:0.8rem; color:#8b949e;">
    <div style="display:flex;align-items:center;gap:6px;margin:4px 0;">
        <span class="severity-dot sev-CRITICAL"></span> CRITICAL (9.0-10.0)
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin:4px 0;">
        <span class="severity-dot sev-HIGH"></span> HIGH (7.0-8.9)
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin:4px 0;">
        <span class="severity-dot sev-MEDIUM"></span> MEDIUM (4.0-6.9)
    </div>
    <div style="display:flex;align-items:center;gap:6px;margin:4px 0;">
        <span class="severity-dot sev-LOW"></span> LOW (0.0-3.9)
    </div>
</div>
"""


def tree_node_html(
    node: dict,
    vuln_map: dict[str, dict],
    expanded: bool = False,
) -> str:
    """Render a single tree node as HTML.

    Args:
        node: Tree node dict with pname, drv_path, children.
        vuln_map: Dict mapping drv_path to vulnerability info.
        expanded: Whether children are initially shown.

    Returns:
        HTML string for this node and its children.
    """
    pname = node.get("pname", "unknown")
    drv_path = node.get("drv_path", "")
    children = node.get("children", [])
    has_children = len(children) > 0

    # Determine severity
    vuln_info = vuln_map.get(drv_path, {})
    severity = "NONE"
    if vuln_info:
        cvss_scores = vuln_info.get("cvssv3_basescore", {})
        max_score = max(cvss_scores.values()) if cvss_scores else 0.0
        if max_score >= 9.0:
            severity = "CRITICAL"
        elif max_score >= 7.0:
            severity = "HIGH"
        elif max_score >= 4.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

    node_id = f"node-{drv_path.replace('/', '_').replace('.', '_')}"
    expand_class = "expanded" if expanded else ""
    leaf_class = "leaf" if not has_children else ""

    if has_children:
        html = f"""<div class="tree-node" id="{node_id}">
    <div class="tree-node-header" onclick="toggleNode('{node_id}')">
        <span class="expand-icon {expand_class} {leaf_class}">&#9654;</span>
        <span class="severity-dot sev-{severity}"></span>
        <span class="pkg-name">{pname}</span>
        <span class="sev-label">{severity}</span>
    </div>
    <div class="tree-children {expand_class}" id="{node_id}-children">"""
        for child in children:
            html += tree_node_html(child, vuln_map, expanded=False)
        html += """</div>
</div>"""
    else:
        html = f"""<div class="tree-node" id="{node_id}">
    <div class="tree-node-header">
        <span class="expand-icon {leaf_class}">&#9654;</span>
        <span class="severity-dot sev-{severity}"></span>
        <span class="pkg-name">{pname}</span>
        <span class="sev-label">{severity}</span>
    </div>
</div>"""
    return html


def tree_html(scan_id: int, vuln_map: dict[str, dict]) -> str:
    """Render the full dependency tree as inner HTML.

    Args:
        scan_id: Scan ID.
        vuln_map: Dict mapping drv_path to vulnerability info.

    Returns:
        HTML string for the tree (to be wrapped by base_html).
    """
    return f"""<h2>Dependency Tree</h2>
<div id="tree-root"
     hx-get="/api/tree/{scan_id}"
     hx-trigger="load"
     hx-swap="innerHTML"
     hx-target="this">
</div>
<script>
function toggleNode(id) {{
    const children = document.getElementById(id + '-children');
    const icon = document.querySelector('#' + id + ' .expand-icon');
    if (children) {{
        children.classList.toggle('expanded');
        if (icon) icon.classList.toggle('expanded');
    }}
}}
</script>"""
