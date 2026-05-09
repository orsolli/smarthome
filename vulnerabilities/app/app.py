"""Entry point for the vulnerability scanning service.

Ties together the ScanPipeline orchestrator and database queries
to run scans and serve results via a Bottle web server.
"""

import argparse
import sys
from pathlib import Path

from bottle import Bottle, request, run  # type: ignore

from core import database
from core import timeseries
from core.database_storage import DatabaseStorage
from core.scanner import ScanPipeline
from app.api import (
    api_scans_endpoint,
    api_tree_endpoint,
    api_vuln_map_endpoint,
    scan_detail_endpoint,
)

app = Bottle()

# Default database path (writable location)
import os

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    str(
        Path.home()
        / ".local"
        / "share"
        / "vulnerabilities"
        / "vulnerabilities.db"
    ),
)
_DB_DIR = Path(DB_PATH).parent
_DB_DIR.mkdir(parents=True, exist_ok=True)

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


@app.get("/timeseries")
def timeseries_endpoint():
    """Get vulnerability timeseries for chart rendering.

    Query params:
        package: Optional package name filter. If omitted, returns all packages.
        since: Start timestamp (ISO format).
        until: Optional end timestamp (ISO format).

    Returns:
        JSON list of timeline rows for charting.
    """
    since = request.params.get("since", "2000-01-01")
    until = request.params.get("until")
    package = request.params.get("package")

    conn = database.init_db(DB_PATH)
    if package:
        data = timeseries.get_timeseries_for_package(conn, package, since, until)
    else:
        data = timeseries.get_timeseries_for_all_packages(conn, since, until)
    conn.close()
    return data


@app.get("/tree/<scan_id:int>")
def tree_endpoint(scan_id: int):
    """Get the dependency tree for a scan (JSON format).

    Args:
        scan_id: The scan ID.

    Returns:
        JSON list of dependency tree nodes.
    """
    conn = database.init_db(DB_PATH)
    tree = database.get_dependency_tree_for_scan(conn, scan_id)
    conn.close()
    return tree


@app.get("/aggregation/<scan_id:int>/<package_name>")
def aggregation_endpoint(scan_id: int, package_name: str):
    """Get aggregated severity for a package in a scan.

    Args:
        scan_id: The scan ID.
        package_name: Package name.

    Returns:
        JSON dict with max_severity, scan_count, latest_severity.
    """
    conn = database.init_db(DB_PATH)
    agg = timeseries.get_aggregated_severity(conn, scan_id, package_name)
    conn.close()
    return agg


@app.get("/health")
def health_endpoint():
    """Health check endpoint.

    Returns:
        JSON health status.
    """
    return {"status": "ok"}


@app.get("/api/scans")
def _api_scans():
    """HTMX endpoint: list of scans for sidebar."""
    return api_scans_endpoint()


@app.get("/api/tree/<scan_id:int>")
def _api_tree(scan_id: int):
    """HTMX endpoint: HTML dependency tree."""
    return api_tree_endpoint(scan_id)


@app.get("/api/vuln-map/<scan_id:int>")
def _api_vuln_map(scan_id: int):
    """HTMX endpoint: JSON vulnerability map."""
    return api_vuln_map_endpoint(scan_id)


@app.get("/scan/<scan_id:int>")
def _scan_detail(scan_id: int):
    """HTMX endpoint: scan detail page."""
    return scan_detail_endpoint(scan_id)


def main():
    """Run the Bottle server."""
    # Initialize database on startup
    database.init_db(DB_PATH).close()
    run(app, host="localhost", port=8080, debug=True)


def cli_main() -> None:
    """CLI entry point for vuln-scanner.

    Parses --target argument and runs a scan.
    """
    parser = argparse.ArgumentParser(
        description="Run a vulnerability scan on a Nix derivation target."
    )
    parser.add_argument(
        "--target",
        default="/run/current-system",
        help="Target derivation path to scan (default: /run/current-system)",
    )
    args = parser.parse_args()

    result = run_scan(args.target)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"Scan ID: {result['scan_id']}")
    print(f"Target: {result['target']}")
    print(f"Vulnerabilities found: {result['vulnerabilities_found']}")
    for vuln in result.get("vulnerabilities", []):
        print(f"  - {vuln['package_name']} ({vuln['severity']})")


if __name__ == "__main__":
    main()
