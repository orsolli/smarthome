"""Mock module simulating `vulnix` scanner output.

Implements VulnerabilityScannerInterface for development use.
"""

from typing import Any

from interfaces import VulnerabilityScannerInterface


# Simulated vulnix scan output
DEMO_VULNERABILITIES: list[dict[str, Any]] = [
    {
        "name": "Diff-1.0.2",
        "pname": "Diff",
        "version": "1.0.2",
        "derivation": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
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
        "name": "ShellCheck-0.11.0",
        "pname": "ShellCheck",
        "version": "0.11.0",
        "derivation": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
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
        return DEMO_VULNERABILITIES
