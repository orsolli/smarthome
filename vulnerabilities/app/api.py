"""API endpoints for the vulnerability frontend.

Provides HTMX-compatible endpoints for:
- /: one row per scanned target
- /scan/<scan_id>: a generation view, ?days= zooms the timeline window
- /api/tree/<scan_id>: HTML dependency tree
- /api/bars/<scan_id>: timeline bars for the roots and their children
- /api/bars/<scan_id>/<drv_path>: timeline bars for a node's children
- /api/children/<scan_id>/<drv_path>: children beyond the visible limit
- /api/vuln-map/<scan_id>: JSON vulnerability map
"""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime

from app.chart import mini_bar_html
from app.templates import base_html, node_dom_id, sidebar_html, tree_html, window_url
from core import database, timeseries
from core.severity import severity_rank


def _get_db():
    """A connection to the database this app is configured to use."""
    return database.init_db()


def index_endpoint():
    """Landing page: every scanned target, newest first."""
    with closing(_get_db()) as conn:
        targets = database.list_targets(conn)

    if targets:
        newest = targets[0]
        main = (
            f"<h2>{newest['target']}</h2>"
            f"<p>{newest['scan_count']} scans, most recent on "
            f"{newest['last_scan'][:10]}. "
            f'<a href="/scan/{newest["latest_scan_id"]}">Open the dependency tree</a>.</p>'
        )
    else:
        main = (
            "<h2>No scans yet</h2>"
            "<p>Run <code>python -m app scan --target /run/current-system</code> "
            "to fill the database.</p>"
        )

    return base_html("Vulnerability Scanner", sidebar_html(targets), main)


MAX_VISIBLE_CHILDREN = 50


def _children_map(nodes: list[dict]) -> dict[str, list[dict]]:
    """Map parent node id -> list of child nodes."""
    children: dict[str, list[dict]] = {}
    for node in nodes:
        parent_id = node.get("parent_id")
        if parent_id is not None:
            children.setdefault(str(parent_id), []).append(node)
    return children


def _vuln_map(conn, scan_id: int) -> dict[str, str]:
    """drv_path -> severity for a scan's vulnerability events."""
    return {
        drv_path: severity
        for drv_path, severity in conn.execute(
            "SELECT drv_path, severity FROM vulnerability_events WHERE scan_id = ?",
            (scan_id,),
        )
    }


def _subtree_severities(
    nodes: list[dict],
    vuln_map: dict[str, str],
) -> dict[str, str]:
    """Aggregated severity per node: a node is as red as its worst descendant."""
    return {
        str(node_id): severity
        for node_id, (severity, _) in timeseries.subtree_worst(nodes, vuln_map).items()
    }


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


@dataclass
class ScanContext:
    """One scan's structure, severities and timeline, computed once per request.

    The tree, the bars and the "show more" response all need the same five
    things, and each of them is cheap enough to rebuild but expensive enough
    that a single node expansion should not do it twice.
    """

    scan_id: int
    days: int | None
    nodes: list[dict]
    children: dict[str, list[dict]]
    severity: dict[str, str]
    start: datetime
    end: datetime
    timelines: dict[str, list[dict]]

    def roots(self) -> list[dict]:
        """Tree roots, worst subtree first, then by derivation path."""
        return sorted(
            (node for node in self.nodes if node.get("parent_id") is None),
            key=lambda n: (
                -severity_rank(self.severity.get(str(n["id"]), "NONE")),
                n["drv_path"],
            ),
        )

    def node(self, drv_path: str) -> dict | None:
        """Node by derivation path, or None when the scan has no such node."""
        return next((node for node in self.nodes if node["drv_path"] == drv_path), None)

    def ordered_children(self, node: dict) -> list[dict]:
        """Children of `node`, worst subtree first."""
        return _ordered_children(node, self.children, self.severity)


def _scan_context(conn, scan_id: int, days: int | None) -> ScanContext | None:
    """Fetch everything a page or a lazy fragment needs about one scan.

    Args:
        conn: Database connection.
        scan_id: Scan whose dependency tree defines the structure.
        days: Window length in days; None spans every scan of the target.

    Returns:
        ScanContext, or None when the scan has no tree.
    """
    nodes = database.get_dependency_tree_for_scan(conn, scan_id)
    if not nodes:
        return None
    severity = _subtree_severities(nodes, _vuln_map(conn, scan_id))
    since, start, end = timeseries.get_zoom_window(conn, scan_id, days)
    return ScanContext(
        scan_id=scan_id,
        days=days,
        nodes=nodes,
        children=_children_map(nodes),
        severity=severity,
        start=start,
        end=end,
        timelines=timeseries.get_tree_subtree_timelines(conn, scan_id, since=since),
    )


def _drv_path(drv_path: str) -> str:
    """Derivation path as it appears in an HTMX URL, which drops the leading slash.

    Bottle consumes the separator slash between route segments, so the path
    arrives without it and has to be restored before it is looked up.
    """
    return drv_path if drv_path.startswith("/") else "/" + drv_path


def _render_node(ctx: ScanContext, node: dict, offset: int = 0) -> str:
    """Render one tree node, its empty timeline slot, and its children.

    Nodes with more than MAX_VISIBLE_CHILDREN children are truncated and
    get a "show more" button that loads the rest lazily.

    Args:
        ctx: The scan the node belongs to.
        node: Tree node dict.
        offset: Number of children to skip (for the "show more" response).

    Returns:
        HTML string for the node.
    """
    node_id = node_dom_id(node["drv_path"])
    drv_path = node["drv_path"]
    sev = ctx.severity.get(str(node["id"]), "NONE")
    children = ctx.ordered_children(node)
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
        url_path = drv_path.lstrip("/")
        html += f'  <div class="tree-children" id="{node_id}-children"\n'
        html += f'    hx-get="{window_url(f"/api/bars/{ctx.scan_id}/{url_path}", ctx.days)}"\n'
        html += '    hx-trigger="node-expanded"\n'
        html += '    hx-swap="none">\n'
        for child in children[offset:offset + MAX_VISIBLE_CHILDREN]:
            html += _render_node(ctx, child)
        remaining = len(children) - offset - MAX_VISIBLE_CHILDREN
        if remaining > 0:
            html += (
                f'    <button class="show-more" '
                f'hx-get="{window_url(f"/api/children/{ctx.scan_id}/{url_path}", ctx.days, offset=offset + MAX_VISIBLE_CHILDREN)}" '
                f'hx-target="#{node_id}-children" hx-swap="beforeend" '
                f'hx-trigger="click">show {remaining} more children</button>\n'
            )
        html += "  </div>\n"

    html += "</div>"
    return html


def api_tree_endpoint(scan_id: int, days: int | None = None) -> str:
    """Get dependency tree as HTML for a scan.

    Args:
        scan_id: Scan to render.
        days: Timeline window in days, carried into the lazy bar requests so
            a newly expanded node is zoomed like the rest of the page.
    """
    with closing(_get_db()) as conn:
        ctx = _scan_context(conn, scan_id, days)

    if ctx is None:
        return "<p>No tree data available for this scan.</p>"

    result = "".join(_render_node(ctx, root) for root in ctx.roots())

    # Fill the roots' and their children's bars once the tree is in the DOM
    result += (
        f'<div id="bars-bootstrap" hx-get="{window_url(f"/api/bars/{scan_id}", days)}" '
        'hx-trigger="load" hx-swap="none"></div>'
    )
    return result


def api_vuln_map_endpoint(scan_id: int) -> dict[str, dict[str, str]]:
    """Get vulnerability map as JSON for a scan: drv_path -> package and severity."""
    with closing(_get_db()) as conn:
        return {
            row["drv_path"]: {
                "package_name": row["package_name"],
                "severity": row["severity"],
            }
            for row in conn.execute(
                "SELECT drv_path, package_name, severity FROM vulnerability_events WHERE scan_id = ?",
                (scan_id,),
            )
        }


def _bars_html(ctx: ScanContext, nodes: list[dict]) -> str:
    """Out-of-band HTML filling the timeline slot of each given node."""
    return "".join(
        f'<div id="{node_dom_id(node["drv_path"])}-timeline" class="node-timeline" '
        'hx-swap-oob="true">'
        f'{mini_bar_html(ctx.timelines.get(node["drv_path"], []), ctx.start, ctx.end)}'
        f"</div>"
        for node in nodes
    )


def api_bars_endpoint(
    scan_id: int,
    drv_path: str | None = None,
    days: int | None = None,
) -> str:
    """HTMX out-of-band bars for a node's children (roots on tree load).

    Only nodes that are in the DOM get a bar: a node's children beyond
    MAX_VISIBLE_CHILDREN are not rendered yet, and their bars arrive with the
    "show more" response that renders them.

    Args:
        scan_id: Scan whose dependency tree defines the structure.
        drv_path: Derivation path of the expanded node. Omit for the
            bootstrap request, which fills the roots and their children.
            The HTMX URL embeds it without its leading slash, since
            Bottle consumes the separator slash between route segments.
        days: Window length in days; None spans every scan of the target.

    Returns:
        HTML string of out-of-band timeline divs.
    """
    with closing(_get_db()) as conn:
        ctx = _scan_context(conn, scan_id, days)

    if ctx is None:
        return ""

    if drv_path is None:
        roots = ctx.roots()
        targets = list(roots)
        for root in roots:
            targets.extend(ctx.ordered_children(root)[:MAX_VISIBLE_CHILDREN])
    else:
        parent = ctx.node(_drv_path(drv_path))
        if parent is None:
            return ""
        targets = ctx.ordered_children(parent)[:MAX_VISIBLE_CHILDREN]

    return _bars_html(ctx, targets)


def api_children_endpoint(
    scan_id: int,
    drv_path: str,
    offset: int = MAX_VISIBLE_CHILDREN,
    days: int | None = None,
) -> str:
    """HTMX response: children of a node beyond the visible limit, with bars.

    Args:
        scan_id: Scan whose dependency tree defines the structure.
        drv_path: Derivation path of the node whose children are requested.
        offset: Number of already-rendered children to skip.
        days: Window length in days; None spans every scan of the target.

    Returns:
        HTML string: the remaining tree nodes plus their timeline bars.
    """
    with closing(_get_db()) as conn:
        ctx = _scan_context(conn, scan_id, days)

    if ctx is None:
        return ""

    parent = ctx.node(_drv_path(drv_path))
    if parent is None:
        return ""

    hidden = ctx.ordered_children(parent)[offset:]
    return "".join(_render_node(ctx, child) for child in hidden) + _bars_html(ctx, hidden)


def scan_detail_endpoint(scan_id: int, days: int | None = None):
    """Render one generation of a target: tree, bars and window controls.

    Args:
        scan_id: Scan to view.
        days: Optional window length in days, from ?days= on the URL.
    """
    with closing(_get_db()) as conn:
        scan = conn.execute(
            "SELECT id, timestamp, target, scanned_path FROM scans WHERE id = ?",
            (scan_id,),
        ).fetchone()
        targets = database.list_targets(conn)

    if not scan:
        return base_html(
            "Scan not found",
            sidebar_html(targets),
            "<h1>Scan not found</h1>",
        )

    scan = dict(scan)
    return base_html(
        f"Scan {scan['id']}: {scan['target']}",
        sidebar_html(targets, scan, days),
        tree_html(scan_id, days),
    )
