"""Entry point for the vulnerability scanning service.

Ties together the ScanPipeline orchestrator and database queries
to run scans and serve results via a Bottle web server.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from bottle import Bottle, request, response, run  # type: ignore

from core import database
from core import timeseries
from core.database_storage import DatabaseStorage
from core.scanner import ScanPipeline
from app.api import (
    MAX_VISIBLE_CHILDREN,
    api_bars_endpoint,
    api_children_endpoint,
    api_tree_endpoint,
    api_vuln_map_endpoint,
    index_endpoint,
    scan_detail_endpoint,
)

app = Bottle()


def _json_response(data) -> str:
    """Serialize a dict or list payload and mark it as JSON.

    Bottle 0.13's JSON plugin only auto-serializes dict return values,
    so list-returning endpoints must serialize explicitly.
    """
    response.content_type = "application/json"
    return json.dumps(data)

# Default database path (writable location)
DB_PATH = database.default_db_path()
_DB_DIR = Path(DB_PATH).parent
_DB_DIR.mkdir(parents=True, exist_ok=True)

# Initialize the scan pipeline with production storage
_storage = DatabaseStorage(DB_PATH)
pipeline = ScanPipeline.default()
pipeline.storage = _storage  # Replace mock storage with real storage


def run_scan(
    target: str,
    label: str | None = None,
    timestamp: str | None = None,
) -> dict:
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
        label: Identity the scan is recorded under (defaults to target).
        timestamp: ISO timestamp to record, for backfilling old generations.

    Returns:
        Dict with scan results summary.
    """
    return pipeline.run_scan(target, label=label, timestamp=timestamp)


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

    return _json_response(vulns)


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
    return _json_response(data)


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
    return _json_response(tree)


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


def _days_param() -> int | None:
    """Window length in days from the query string, None for the whole history."""
    raw = request.query.get("days")
    return int(raw) if raw and raw.isdigit() else None


@app.get("/")
def _index():
    """Landing page: one row per scanned target."""
    return index_endpoint()


@app.get("/api/tree/<scan_id:int>")
def _api_tree(scan_id: int):
    """HTMX endpoint: HTML dependency tree."""
    return api_tree_endpoint(scan_id, _days_param())


@app.get("/api/vuln-map/<scan_id:int>")
def _api_vuln_map(scan_id: int):
    """HTMX endpoint: JSON vulnerability map."""
    return api_vuln_map_endpoint(scan_id)


@app.get("/api/bars/<scan_id:int>")
def _api_bars(scan_id: int):
    """HTMX endpoint: timeline bars for the roots and their children."""
    return api_bars_endpoint(scan_id, days=_days_param())


@app.get("/api/bars/<scan_id:int>/<drv_path:path>")
def _api_bars_node(scan_id: int, drv_path: str):
    """HTMX endpoint: timeline bars for a node's children."""
    return api_bars_endpoint(scan_id, drv_path, _days_param())


@app.get("/api/children/<scan_id:int>/<drv_path:path>")
def _api_children(scan_id: int, drv_path: str):
    """HTMX endpoint: children of a node beyond the visible limit."""
    offset = int(request.query.get("offset", MAX_VISIBLE_CHILDREN))
    return api_children_endpoint(scan_id, drv_path, offset, _days_param())


@app.get("/scan/<scan_id:int>")
def _scan_detail(scan_id: int):
    """One generation of a target, with the timeline window from ?days=."""
    return scan_detail_endpoint(scan_id, _days_param())


def main():
    """Run the Bottle server."""
    # Initialize database on startup
    database.init_db(DB_PATH).close()
    host, port = os.environ.get("BIND_ADDRESS", "localhost:8080").split(":")
    run(app, host=host, port=int(port), debug=True)


def cli_main(argv: list[str] | None = None) -> int:
    """CLI entry point for vuln-scanner.

    Parses --target and runs a scan.

    Args:
        argv: Argument list, defaults to sys.argv[1:].

    Returns:
        Process exit code: 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Run a vulnerability scan on a Nix derivation target."
    )
    parser.add_argument(
        "--target",
        default="/run/current-system",
        help="Target derivation path to scan (default: /run/current-system)",
    )
    parser.add_argument(
        "--as-target",
        default=None,
        help=(
            "Identity to record the scan under. Lets an old Nix generation "
            "(a different derivation of the same system) join the timeline of "
            "another target, e.g. --target /nix/var/nix/profiles/system-2-link "
            "--as-target /run/current-system"
        ),
    )
    parser.add_argument(
        "--at",
        default=None,
        help=(
            "ISO timestamp to record instead of now, for backfilling a "
            "generation with the date it was activated"
        ),
    )
    args = parser.parse_args(argv)

    result = run_scan(args.target, label=args.as_target, timestamp=args.at)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    print(f"Scan ID: {result['scan_id']}")
    print(f"Target: {result['target']}")
    scanned = result.get("scanned_path", result["target"])
    if scanned != result["target"]:
        print(f"Scanned path: {scanned}")
    if result.get("timestamp"):
        print(f"Recorded at: {result['timestamp']}")
    print(f"Vulnerabilities found: {result['vulnerabilities_found']}")
    for vuln in result.get("vulnerabilities", []):
        print(f"  - {vuln['package_name']} ({vuln['severity']})")
    return 0


if __name__ == "__main__":
    main()
