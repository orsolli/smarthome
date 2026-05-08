"""Mock module simulating `nix why-depends` output.

Implements DependencyMapperInterface for development use.
"""

from typing import Any

from interfaces import DependencyMapperInterface


# Simulated dependency tree structures
DEMO_DEPENDENCY_TREES: dict[tuple[str, str], str] = {
    (
        "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
        "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
    ): """/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv
    └───/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv
        └───/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv""",
    (
        "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
        "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
    ): """/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv
    └───/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv""",
    (
        "/nix/store/f8w6rdvahz02m1qlmv7fwvkljb1i1aq2-vulnerabilities-0.1.drv",
        "/nix/store/7whqc6b2wdxd3rz141vnsfizcxbizcnh-ed-1.22.5.drv",
    ): """/nix/store/f8w6rdvahz02m1qlmv7fwvkljb1i1aq2-vulnerabilities-0.1.drv
└───/nix/store/q2xn5647kadsgpz40xcmjssa0pmdmiwi-stdenv-linux.drv
    └───/nix/store/7whqc6b2wdxd3rz141vnsfizcxbizcnh-ed-1.22.5.drv""",
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
