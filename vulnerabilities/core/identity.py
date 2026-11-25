"""Stable identity of a dependency-tree node across scans.

A Nix derivation path embeds a store hash that changes on every rebuild, so
`drv_path` can never match a node from an older scan. Scans are grouped by the
`target` they were run on, and a node within a target is identified by its
package name, its version and a *compressed lineage*: the chain of names from
the nearest ancestor whose name occurs exactly once in that scan's tree, down
to the node.

    /nix/store/<hash>-gcc-9.99.0.drv under strata
        -> lineage "/run/current-system/strata/gcc", version "9.99.0"

Raw lineage paths are not used because `nix why-depends` reports the shortest
dependency path, which drifts between rebuilds ("stdenv-linux" becomes
"stdenv-linux-no-cc"). Anchoring at the nearest unambiguous ancestor keeps the
key stable while still distinguishing the three different gcc nodes of one tree.
"""

import re
from typing import Any


def _drv_stem(drv_path: str) -> str:
    """Name-and-version part of a derivation path, without the store hash."""
    filename = drv_path.rsplit("/", 1)[-1]
    if filename.endswith(".drv"):
        filename = filename[:-4]
    match = re.match(r"^[0-9a-z]{20,}-(.*)$", filename)
    return match.group(1) if match else filename


def version_from_drv(drv_path: str, package_name: str) -> str:
    """Version of a derivation, everything after the base package name.

    A store name is `<base>-<version>`, but the package name vulnix reports
    already contains the version ('glibc-2.42'), so the base name is recovered
    by dropping that trailing numeric part. The rest of the store name is then
    the version, including revision and variant suffixes.

    Args:
        drv_path: Derivation path.
        package_name: Name already extracted from the same path.

    Returns:
        '9.99.0' for '...-gcc-9.99.0.drv', '9.99-11' for
        '...-glibc-9.99-11.drv', '' when there is no version suffix.
    """
    stem = _drv_stem(drv_path)
    base = package_name
    match = re.match(r"^(.+)-(\d.*)$", package_name)
    if match:
        base = match.group(1)
    if base and stem.startswith(base) and len(stem) > len(base):
        return stem[len(base):].lstrip("-")
    return ""


def compressed_lineages(
    nodes: list[dict[str, Any]],
    root_label: str,
) -> dict[int, str]:
    """Compute the compressed lineage of every node of one scan's tree.

    Args:
        nodes: Nodes of a single scan: dicts with id, package_name, parent_id.
        root_label: Label standing in for the volatile root derivation name,
            normally the scan's target. It is never part of the returned key
            except for the root node itself.

    Returns:
        Dict mapping node id -> lineage string, e.g.
        '/run/current-system/system-path/ntfy-sh/curl'.
    """
    names = {node["id"]: node.get("package_name") or "" for node in nodes}
    parents = {node["id"]: node.get("parent_id") for node in nodes}

    counts: dict[str, int] = {}
    for name in names.values():
        counts[name] = counts.get(name, 0) + 1

    lineages: dict[int, str] = {}
    for node in nodes:
        chain: list[str] = []
        current = node["id"]
        while current is not None and current in names:
            chain.append(names[current])
            current = parents.get(current)
        chain.reverse()  # root .. node

        if len(chain) == 1:
            lineages[node["id"]] = root_label
            continue

        anchor = None
        for index in range(len(chain) - 2, 0, -1):
            if counts[chain[index]] == 1:
                anchor = index
                break

        lineages[node["id"]] = "/".join(
            [root_label] + chain[anchor if anchor is not None else 1:]
        )

    return lineages
