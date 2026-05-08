"""Real implementations of pipeline stages using actual Nix tooling.

Activated when VULNIX_PATH environment variable is set.
"""

import json
import os
import subprocess
from typing import Any

from interfaces import (
    DependencyMapperInterface,
    DerivationSourceInterface,
    VulnerabilityScannerInterface,
)


class RealDerivationSource(DerivationSourceInterface):
    """Uses `nix derivation show` to resolve target to derivation.

    Returns a dict mapping drv_path -> {"drv_path": str, "output_path": str}.
    """

    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        result = subprocess.run(
            ["nix", "derivation", "show", target],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return {}
        data = json.loads(result.stdout)
        # nix derivation show v4 wraps derivations under a "derivations" key
        if isinstance(data, dict) and "derivations" in data:
            data = data["derivations"]
        # Enrich with output path from each derivation's outputs
        for drv_path, info in data.items():
            if isinstance(info, dict):
                outputs = info.get("outputs", {})
                if isinstance(outputs, dict):
                    out_path = outputs.get("out", {}).get("path", "")
                    info["output_path"] = out_path
        return data


class RealVulnerabilityScanner(VulnerabilityScannerInterface):
    """Uses vulnix to scan for vulnerabilities."""

    def scan_vulnerabilities(self, target: str) -> list[dict[str, Any]]:
        vulnix_path = os.environ.get("VULNIX_PATH", "")
        if not vulnix_path:
            return []
        # target may be a drv_path or an output_path; try output first
        result = subprocess.run(
            [vulnix_path, "-j", target],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []


class RealDependencyMapper(DependencyMapperInterface):
    """Uses `nix why-depends` to trace dependency paths."""

    def why_depends(
        self, system_derivation: str, target_derivation: str
    ) -> str:
        # Ensure paths are absolute /nix/store paths
        if not system_derivation.startswith("/"):
            system_derivation = f"/nix/store/{system_derivation}"
        if not target_derivation.startswith("/"):
            target_derivation = f"/nix/store/{target_derivation}"
        result = subprocess.run(
            ["nix", "why-depends", system_derivation, target_derivation],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout
