"""Mock module simulating `nix why-depends` output.

Implements DependencyMapperInterface for development use.
"""

from typing import Any

from interfaces import DependencyMapperInterface


# Simulated dependency tree structures
DEMO_DEPENDENCY_TREES: dict[tuple[str, str], str] = {
    (
        "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
        "/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv",
    ): """/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
└───/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv
    └───/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv
        └───/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv""",
    (
        "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
        "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
    ): """/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
└───/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv
    └───/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv""",
    (
        "/nix/store/vulndrv0000000000000000000000000000-vulnerabilities-0.1.drv",
        "/nix/store/eddrv000000000000000000000000000000-ed-9.99.0.drv",
    ): """/nix/store/vulndrv0000000000000000000000000000-vulnerabilities-0.1.drv
└───/nix/store/stddrv000000000000000000000000000000-stdenv-linux.drv
    └───/nix/store/eddrv000000000000000000000000000000-ed-9.99.0.drv""",
}


class MockDependencyMapper(DependencyMapperInterface):
    """Mock implementation of DependencyMapperInterface."""

    def why_depends(
        self, system_derivation: str, target_derivation: str
    ) -> str:
        """Return the demo dependency tree.

        Args:
            system_derivation: The system derivation path.
            target_derivation: The target derivation path.

        Returns:
            A list of dependency tree nodes.
        """
        key = (system_derivation, target_derivation)
        return DEMO_DEPENDENCY_TREES.get(key, "")
