"""HTML templates for the vulnerability frontend."""

import re

from app.colors import SEVERITY_COLORS


def node_dom_id(drv_path: str) -> str:
    """DOM id for a tree node: a bare CSS identifier.

    Args:
        drv_path: Derivation path of the node.

    Returns:
        The id, with everything outside [A-Za-z0-9_-] flattened to "_".

    HTMX resolves an out-of-band swap with `#<id>`, so an id carrying
    characters like `+` or `=` (webkitgtk-9.99.0+abi=1.0.drv) silently
    fails to match and the node keeps an empty timeline.
    """
    return "node-" + re.sub(r"[^A-Za-z0-9_-]", "_", drv_path)


def window_url(path: str, days: int | None = None, **params) -> str:
    """URL for a page or a lazy HTMX request, carrying the zoom window.

    Args:
        path: Path without a query string.
        days: Window length in days; None means the whole history, so no
            parameter is written at all.
        params: Further query parameters, in order.

    Returns:
        The URL, with `days=N` first when a window is in effect.
    """
    query = [("days", days)] if days else []
    query.extend(params.items())
    return f"{path}?{'&'.join(f'{key}={value}' for key, value in query)}" if query else path


def _severity_css() -> str:
    """CSS rules for the severity dots, derived from the color table."""
    return "\n        ".join(
        f".sev-{severity} {{ background: {color}; box-shadow: 0 0 6px {color}80; }}"
        for severity, (color, _) in SEVERITY_COLORS.items()
    )


def base_html(title: str, sidebar: str = "", main: str = "") -> str:
    """Render the base HTML page.

    Args:
        title: Page title.
        sidebar: Navigation column: targets, window chips, legend.
        main: Content column, usually a dependency tree.

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
        {_severity_css()}
        .pkg-name {{ font-size: 0.85rem; }}
        .sev-label {{ font-size: 0.7rem; color: #8b949e; margin-left: auto; }}
        #chart-container {{ margin-top: 20px; }}
        .chart-bar {{ display: flex; align-items: center; margin: 2px 0; font-size: 0.75rem; }}
        .chart-bar-label {{ width: 100px; color: #8b949e; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .chart-bar-track {{ flex: 1; height: 16px; background: #21262d; border-radius: 3px; overflow: hidden; display: flex; }}
        .chart-bar-segment {{ height: 100%; transition: width 0.3s; }}
        .node-timeline {{ margin: 2px 0 6px 26px; }}
        .node-timeline:empty {{ display: none; }}
        .node-timeline .chart-bar-label {{ display: none; }}
        .node-timeline .chart-bar-track {{ height: 10px; }}
        .show-more {{ margin: 6px 0 0 26px; font-size: 0.75rem; color: #58a6ff; background: none; border: 1px solid #30363d; border-radius: 4px; padding: 4px 8px; cursor: pointer; }}
        .show-more:hover {{ background: #21262d; }}
        .target-item {{ display: flex; align-items: center; gap: 8px; padding: 6px 8px; margin: 4px 0; font-size: 0.8rem; background: #1c2128; border-radius: 4px; }}
        .target-item a {{ color: #58a6ff; text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .target-item:hover {{ background: #21262d; }}
        .target-meta {{ margin-left: auto; font-size: 0.7rem; color: #8b949e; white-space: nowrap; }}
        .window-chips {{ display: flex; gap: 6px; margin: 10px 0; flex-wrap: wrap; }}
        .chip {{ font-size: 0.75rem; color: #8b949e; background: #21262d; border: 1px solid #30363d; border-radius: 4px; padding: 4px 8px; text-decoration: none; }}
        .chip:hover {{ color: #c9d1d9; }}
        .chip.active {{ background: #58a6ff; color: #0d1117; border-color: #58a6ff; }}
        .gen-info {{ font-size: 0.75rem; color: #8b949e; margin: 8px 0; line-height: 1.4; }}
        .gen-info code {{ color: #c9d1d9; }}
    </style>
</head>
<body>
    <div id="sidebar">
        {sidebar}
    </div>
    <div id="main">
        {main}
    </div>
</body>
</html>"""


WINDOW_CHOICES: tuple[tuple[int | None, str], ...] = (
    (7, "7d"),
    (30, "30d"),
    (90, "90d"),
    (None, "all"),
)


def _short_date(iso: str) -> str:
    """Readable form of an ISO timestamp: 2024-11-17 19:16."""
    if not iso:
        return ""
    return iso[:10] + (" " + iso[11:16] if len(iso) >= 16 else "")


def sidebar_html(
    targets: list[dict],
    scan: dict | None = None,
    days: int | None = None,
) -> str:
    """Navigation column: every scanned target and the current scan's window.

    Args:
        targets: Rows from core.database.list_targets, newest first.
        scan: The scan being viewed (id, target, scanned_path, timestamp), or
            None on the home page.
        days: Length of the current window in days; None is the whole history.

    Returns:
        Sidebar HTML string.
    """
    html = "<h1>Vulnerability Scanner</h1>\n<h2>Targets</h2>\n<div class=\"target-list\">\n"
    if targets:
        for target in targets:
            worst = target["worst_severity"]
            html += (
                f'  <div class="target-item">\n'
                f'    <span class="severity-dot sev-{worst}"></span>\n'
                f'    <a href="/scan/{target["latest_scan_id"]}">{target["target"]}</a>\n'
                f'    <span class="target-meta">{target["scan_count"]}{" scan" if target["scan_count"] == 1 else " scans"} · {_short_date(target["last_scan"])}</span>\n'
                f'  </div>\n'
            )
    else:
        html += '  <div class="target-item">No scans yet</div>\n'
    html += "</div>\n"

    if scan:
        scan_id = scan["id"]
        generation = scan.get("scanned_path") or scan["target"]
        html += f"<h2>Scan {scan_id}</h2>\n"
        html += (
            f'<div class="gen-info">\n'
            f'  <code>{scan["target"]}</code> as of {_short_date(scan["timestamp"])}\n'
            f'  <br>generation <code>{generation}</code>\n'
            f"</div>\n"
            '<div class="window-chips">\n'
        )
        for length, label in WINDOW_CHOICES:
            active = " active" if length == days else ""
            html += f'  <a class="chip{active}" href="{window_url(f"/scan/{scan_id}", length)}">{label}</a>\n'
        html += "</div>\n"

    html += """<h2>Severity Legend</h2>
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
    return html


def tree_html(scan_id: int, days: int | None = None) -> str:
    """Render the dependency tree container with lazy timeline bars.

    Args:
        scan_id: Scan to render.
        days: Timeline window in days; None spans the whole history.

    Returns:
        HTML string for the tree (to be wrapped by base_html).
    """
    return f"""<h2>Dependency Tree</h2>
<div id="tree-root"
     hx-get="{window_url(f'/api/tree/{scan_id}', days)}"
     hx-trigger="load"
     hx-swap="innerHTML"
     hx-target="this">
</div>
<script>
function toggleNode(id) {{
    const children = document.getElementById(id + '-children');
    const icon = document.querySelector('#' + id + ' .expand-icon');
    if (children) {{
        const expanding = !children.classList.contains('expanded');
        children.classList.toggle('expanded');
        if (icon) icon.classList.toggle('expanded');
        if (expanding && window.htmx) htmx.trigger(children, 'node-expanded');
    }}
}}
</script>"""
