"""Mock module simulating `vulnix` scanner output.

Implements VulnerabilityScannerInterface for development use.
"""

from typing import Any

from interfaces import VulnerabilityScannerInterface


# Simulated vulnix scan output
DEMO_VULNERABILITIE1: list[dict[str, Any]] = [
    {
        "name": "Diff-9.99.0",
        "pname": "Diff",
        "version": "9.99.0",
        "derivation": "/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv",
        "affected_by": ["CVE-2024-13278"],
        "whitelisted": [],
        "cvssv3_basescore": {
            "CVE-2024-13278": 9.1,
        },
        "description": {
            "CVE-2024-13278": "Incorrect Authorization vulnerability in Drupal Diff allows Functionality Misuse. This issue affects Diff: from 0.0.0 before 1.8.0."
        },
    },
    {
        "name": "ShellCheck-9.99.0",
        "pname": "ShellCheck",
        "version": "9.99.0",
        "derivation": "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
        "affected_by": ["CVE-2021-28794"],
        "whitelisted": [],
        "cvssv3_basescore": {
            "CVE-2021-28794": 9.8,
        },
        "description": {
            "CVE-2021-28794": "The unofficial ShellCheck extension before 0.13.4 for Visual Studio Code mishandles shellcheck.executablePath."
        },
    },
]

DEMO_VULNERABILITIE2: list[dict[str, Any]] = [
    {
        "name": "ed-9.99.0",
        "pname": "ed",
        "version": "9.99.0",
        "derivation": "/nix/store/eddrv000000000000000000000000000000-ed-9.99.0.drv",
        "affected_by": ["CVE-2021-28794"],
        "whitelisted": [],
        "cvssv3_basescore": {
            "CVE-2021-28794": 9.8,
        },
        "description": {
            "CVE-2021-28794": "The unofficial ShellCheck extension before 0.13.4 for Visual Studio Code mishandles shellcheck.executablePath."
        },
    },
]

class MockVulnerabilityScanner(VulnerabilityScannerInterface):
    """Mock implementation of VulnerabilityScannerInterface."""

    def scan_vulnerabilities(self, target: str) -> list[dict[str, Any]]:
        """Return the demo vulnerabilities.

        Args:
            target: The derivation path to scan (ignored; returns demo data).

        Returns:
            A list of vulnerability records.
        """
        return DEMO_VULNERABILITIE1 if target == '/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv' else DEMO_VULNERABILITIE2
