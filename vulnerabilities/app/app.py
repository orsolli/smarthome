"""Entry point for the vulnerability scanning service.

Ties together the ScanPipeline orchestrator and database queries
to run scans and serve results via a Bottle web server.
"""

from pathlib import Path

from bottle import Bottle, request, run, response  # type: ignore

from core import database
from core.database_storage import DatabaseStorage
from core.scanner import ScanPipeline

app = Bottle()

# Default database path (relative to app location)
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "vulnerabilities.db")

# Initialize the scan pipeline with production storage
_storage = DatabaseStorage(DB_PATH)
pipeline = ScanPipeline.default()
pipeline.storage = _storage  # Replace mock storage with real storage


def run_scan(target: str) -> dict:
    """Run a full vulnerability scan on the given target.

    Delegates to ScanPipeline which orchestrates:
        1. DerivationSource: resolve target to derivation
        2. VulnerabilityScanner: scan for vulnerabilities
        3. DependencyMapper: get dependency trees for each vuln
        4. TreeMerger: merge all trees into one
        5. TreeNormalizer: convert to flat vulnerability records
        6. Storage: persist results

    Args:
        target: The derivation path to scan.

    Returns:
        Dict with scan results summary.
    """
    return pipeline.run_scan(target)


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

    conn = database.init_db(DB_PATH)
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
    conn = database.init_db(DB_PATH)
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
    database.init_db(DB_PATH).close()
    run(app, host="localhost", port=8080, debug=True)


if __name__ == "__main__":
    main()
