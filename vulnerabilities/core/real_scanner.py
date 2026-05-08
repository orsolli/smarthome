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
    """Uses `nix derivation show` to resolve target to derivation."""

    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        result = subprocess.run(
            ["nix", "derivation", "show", target],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return {}
        return json.loads(result.stdout)


class RealVulnerabilityScanner(VulnerabilityScannerInterface):
    """Uses vulnix to scan for vulnerabilities."""

    def scan_vulnerabilities(self, target: str) -> list[dict[str, Any]]:
        vulnix_path = os.environ.get("VULNIX_PATH", "")
        if not vulnix_path:
            return []
        result = subprocess.run(
            [vulnix_path, "scan", "-j", target],
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
        result = subprocess.run(
            ["nix", "why-depends", system_derivation, target_derivation],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return ""
        return result.stdout
