"""Normalizer module for converting dependency trees to flat database records.

Produces a flat list of (package_name, drv_path, severity) tuples
suitable for insertion into the vulnerability_events table.

The normalizer receives vulnerability lookup via a callable parameter
(vuln_lookup) rather than importing mock_vulnix directly. This allows
dependency injection for testing and production use.
"""

from typing import Any, Callable

from mock_vulnix import scan_vulnerabilities


def _find_vuln_info(pname: str, drv_path: str) -> dict[str, Any]:
    """Default vulnerability lookup using mock vulnix data.

    Args:
        pname: Package name to look up.
        drv_path: Derivation path to match.

    Returns:
        Dict with severity info, or empty dict if not found.
    """
    vulns = scan_vulnerabilities("")
    for vuln in vulns:
        if vuln.get("pname") == pname or vuln.get("derivation") == drv_path:
            return vuln
    return {}


def _severity_from_cvss(cvss_score: float) -> str:
    """Convert a CVSS score to a severity label.

    Args:
        cvss_score: CVSS v3 base score.

    Returns:
        Severity label string.
    """
    if cvss_score >= 9.0:
        return "CRITICAL"
    if cvss_score >= 7.0:
        return "HIGH"
    if cvss_score >= 4.0:
        return "MEDIUM"
    return "LOW"


def normalize_tree(
    tree: dict[str, Any],
    vuln_lookup: Callable[[str, str], dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Convert a dependency tree into a flat list of vulnerability records.

    Traverses the tree and for each node with a known vulnerability,
    produces a record suitable for database insertion.

    Args:
        tree: A dependency tree dict from tree_parser.merge_nix_trees.
        vuln_lookup: Optional callable(pname, drv_path) -> dict for
            vulnerability lookup. Must be provided; no default.

    Returns:
        List of dicts with keys: package_name, drv_path, severity.
    """
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    _traverse_tree(tree, records, vuln_lookup, seen)
    return records


def _traverse_tree(
    node: dict[str, Any],
    records: list[dict[str, Any]],
    vuln_lookup: Callable[[str, str], dict[str, Any]] | None = None,
    seen: set[tuple[str, str]] | None = None,
) -> None:
    """Recursively traverse a tree and collect vulnerability records.

    Args:
        node: Current tree node.
        records: Accumulator list for found records.
        vuln_lookup: Optional callable for vulnerability lookup.
        seen: Set of already-seen (pname, drv_path) tuples for dedup.
    """
    pname = node.get("pname", "")
    drv_path = node.get("drv_path", "")

    if not pname and not drv_path:
        return

    # Deduplicate by (pname, drv_path)
    if seen is not None and (pname, drv_path) in seen:
        return
    if seen is not None:
        seen.add((pname, drv_path))

    lookup_fn = vuln_lookup or (lambda p, d: {})
    vuln_info = lookup_fn(pname, drv_path)
    if vuln_info:
        cvss_scores = vuln_info.get("cvssv3_basescore", {})
        max_score = max(cvss_scores.values()) if cvss_scores else 0.0
        severity = _severity_from_cvss(max_score)
        records.append(
            {
                "package_name": pname or drv_path,
                "drv_path": drv_path,
                "severity": severity,
            }
        )

    for child in node.get("children", []):
        _traverse_tree(child, records, vuln_lookup, seen)
