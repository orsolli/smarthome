"""Mock module simulating `nix derivation show` output.

Returns a JSON object mapping derivation paths to their metadata.
"""

import json
from typing import Any


# Simulated derivation output for development
DEMO_DERIVATIONS: dict[str, dict[str, Any]] = {
    "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv": {},
}


def show_derivation(target: str) -> dict[str, dict[str, Any]]:
    """Mock `nix derivation show <target>`.

    Args:
        target: A derivation path (e.g. /run/current-system).

    Returns:
        A dict mapping derivation paths to their metadata.
    """
    return DEMO_DERIVATIONS
