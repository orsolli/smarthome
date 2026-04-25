"""Mock module simulating `nix why-depends` output.

Returns a dependency graph tree representing which packages are affected
by a vulnerable package.
"""

from typing import Any


# Simulated dependency tree structures
DEMO_DEPENDENCY_TREES: dict[tuple[str, str], list[dict[str, Any]]] = {
    (
        "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
        "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
    ): [
        {
            "drv_path": "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
            "pname": "nixos-system-OrjanAMD",
            "children": [
                {
                    "drv_path": "/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv",
                    "pname": "pre-switch-checks",
                    "children": [
                        {
                            "drv_path": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
                            "pname": "ShellCheck",
                            "children": [
                                {
                                    "drv_path": "/nix/store/7kwbv6s59ipydz29s086wn73wnnvjrwf-Diff-1.0.2.drv",
                                    "pname": "Diff",
                                    "children": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ],
    (
        "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
        "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
    ): [
        {
            "drv_path": "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv",
            "pname": "nixos-system-OrjanAMD",
            "children": [
                {
                    "drv_path": "/nix/store/zq99dyzglrigchn618wkncr9fxcd5qsc-pre-switch-checks.drv",
                    "pname": "pre-switch-checks",
                    "children": [
                        {
                            "drv_path": "/nix/store/b2cnc4mi1dvmcbsx1fnjfpwrc4srsisp-ShellCheck-0.11.0.drv",
                            "pname": "ShellCheck",
                            "children": [],
                        }
                    ],
                }
            ],
        }
    ],
}


def why_depends(system_derivation: str, target_derivation: str) -> list[dict[str, Any]]:
    """Mock `nix why-depends <system> <target>`.

    Args:
        system_derivation: The system derivation path.
        target_derivation: The target derivation path to check dependencies for.

    Returns:
        A list of dependency tree nodes.
    """
    key = (system_derivation, target_derivation)
    return DEMO_DEPENDENCY_TREES.get(key, [])
