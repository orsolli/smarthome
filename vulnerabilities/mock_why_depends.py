"""Mock module simulating `nix why-depends` output.

Returns a dependency graph tree representing which packages are affected
by a vulnerable package.
"""

from typing import Any


# Simulated dependency tree structures
DEMO_DEPENDENCY_TREES: dict[tuple[str, str], list[dict[str, Any]]] = {
    (
        "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
        "/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv",
    ): [
        {
            "drv_path": "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
            "pname": "nixos-system-example",
            "children": [
                {
                    "drv_path": "/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv",
                    "pname": "pre-switch-checks",
                    "children": [
                        {
                            "drv_path": "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
                            "pname": "ShellCheck",
                            "children": [
                                {
                                    "drv_path": "/nix/store/diffdrv0000000000000000000000000000-Diff-9.99.0.drv",
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
        "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
        "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
    ): [
        {
            "drv_path": "/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv",
            "pname": "nixos-system-example",
            "children": [
                {
                    "drv_path": "/nix/store/chkdrv000000000000000000000000000000-pre-switch-checks.drv",
                    "pname": "pre-switch-checks",
                    "children": [
                        {
                            "drv_path": "/nix/store/shcdrv00000000000000000000000000000-ShellCheck-9.99.0.drv",
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
