"""Normalizer module for converting dependency trees to flat database records.

Produces a flat list of (package_name, drv_path, severity) tuples
suitable for insertion into the vulnerability_events table.
"""

from typing import Any

from mock_vulnix import scan_vulnerabilities


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


def _find_vuln_info(pname: str, drv_path: str) -> dict[str, Any]:
    """Look up vulnerability info for a package from mock vulnix data.

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


def normalize_tree(
    tree: dict[str, Any],
) -> list[dict[str, Any]]:
    """Convert a dependency tree into a flat list of vulnerability records.

    Traverses the tree and for each node with a known vulnerability,
    produces a record suitable for database insertion.

    Args:
        tree: A dependency tree dict from tree_parser.merge_nix_trees.

    Returns:
        List of dicts with keys: package_name, drv_path, severity.
    """
    records: list[dict[str, Any]] = []
    _traverse_tree(tree, records)
    return records


def _traverse_tree(
    node: dict[str, Any],
    records: list[dict[str, Any]],
) -> None:
    """Recursively traverse a tree and collect vulnerability records.

    Args:
        node: Current tree node.
        records: Accumulator list for found records.
    """
    pname = node.get("pname", "")
    drv_path = node.get("drv_path", "")

    if not pname and not drv_path:
        return

    vuln_info = _find_vuln_info(pname, drv_path)
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
        _traverse_tree(child, records)
