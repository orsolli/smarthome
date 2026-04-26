"""Entry point for the vulnerability scanning service.

Ties together mock scanners, merger, normalizer, and database
to run scans and serve results via a Bottle web server.
"""

import sqlite3
from pathlib import Path

from bottle import Bottle, request, run, response

import database
from merger import merge_dependency_trees
from mock_derivation import show_derivation
from mock_vulnix import scan_vulnerabilities
from mock_why_depends import why_depends
from normalizer import normalize_tree

app = Bottle()

# Default database path (relative to app location)
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "vulnerabilities.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection, initializing if needed.

    Returns:
        A sqlite3.Connection instance.
    """
    return database.init_db(DB_PATH)


def run_scan(target: str) -> dict:
    """Run a full vulnerability scan on the given target.

    Steps:
        1. Get derivation info via mock_derivation
        2. Get vulnerabilities via mock_vulnix
        3. Get dependency trees via mock_why_depends
        4. Merge trees via merger
        5. Normalize to flat records via normalizer
        6. Store in database

    Args:
        target: The derivation path to scan.

    Returns:
        Dict with scan results summary.
    """
    conn = get_connection()

    # Step 1: Get derivation
    derivations = show_derivation(target)
    system_derivation = next(iter(derivations), None)
    if not system_derivation:
        return {"error": "No derivation found for target", "target": target}

    # Step 2: Get vulnerabilities
    vulns = scan_vulnerabilities(system_derivation)

    # Step 3: Get dependency trees for each vulnerability
    dep_trees: list[dict] = []
    for vuln in vulns:
        drv = vuln.get("derivation", "")
        tree = why_depends(system_derivation, drv)
        dep_trees.extend(tree)

    # Step 4: Merge trees
    merged = merge_dependency_trees(dep_trees)

    # Step 5: Normalize to flat records
    records = normalize_tree(merged)

    # Step 6: Store in database
    scan_id = database.insert_scan(conn, target)

    event_ids: list[int] = []
    for record in records:
        event_id = database.insert_vulnerability_event(
            conn,
            scan_id,
            record["package_name"],
            record["drv_path"],
            record["severity"],
        )
        event_ids.append(event_id)

        # Store dependency tree nodes
        _store_tree_nodes(conn, scan_id, merged, event_id)

    conn.close()

    return {
        "scan_id": scan_id,
        "target": target,
        "vulnerabilities_found": len(records),
        "vulnerabilities": records,
    }


def _store_tree_nodes(
    conn: sqlite3.Connection,
    scan_id: int,
    tree: dict,
    vuln_event_id: int,
) -> None:
    """Recursively store dependency tree nodes in the database.

    Args:
        conn: Database connection.
        scan_id: The scan ID.
        tree: The dependency tree dict.
        vuln_event_id: Linked vulnerability event ID.
    """
    pname = tree.get("pname", "")
    drv_path = tree.get("drv_path", "")
    if not pname and not drv_path:
        return

    node_id = database.insert_dependency_node(
        conn,
        scan_id,
        pname or drv_path,
        drv_path,
        vulnerability_event_id=vuln_event_id,
    )

    for child in tree.get("children", []):
        _store_tree_nodes(conn, scan_id, child, vuln_event_id)


@app.get("/scan")
def scan_endpoint():
    """Trigger a vulnerability scan.

    Query params:
        target: Derivation path to scan (default: /run/current-system).

    Returns:
        JSON scan results.
    """
    target = request.params.get("target", "/run/current-system")
    result = run_scan(target)
    if "error" in result:
        response.status = 400
    return result


@app.get("/vulnerabilities")
def vulnerabilities_endpoint():
    """Query vulnerability events.

    Query params:
        since: Start timestamp (ISO format).
        until: Optional end timestamp (ISO format).
        package: Optional package name filter.

    Returns:
        JSON list of vulnerability events.
    """
    since = request.params.get("since", "2000-01-01")
    until = request.params.get("until")
    package = request.params.get("package")

    conn = get_connection()
    vulns = database.get_vulnerabilities_since(conn, since, until)
    conn.close()

    if package:
        vulns = [v for v in vulns if v["package_name"] == package]

    return vulns


@app.get("/tree/<scan_id:int>")
def tree_endpoint(scan_id: int):
    """Get the dependency tree for a scan.

    Args:
        scan_id: The scan ID.

    Returns:
        JSON list of dependency tree nodes.
    """
    conn = get_connection()
    tree = database.get_dependency_tree_for_scan(conn, scan_id)
    conn.close()
    return tree


@app.get("/health")
def health_endpoint():
    """Health check endpoint.

    Returns:
        JSON health status.
    """
    return {"status": "ok"}


def main():
    """Run the Bottle server."""
    # Initialize database on startup
    get_connection().close()
    run(app, host="localhost", port=8080, debug=True)


if __name__ == "__main__":
    main()
