"""Mock module simulating `nix derivation show` output.

Implements DerivationSourceInterface for development use.
"""

from typing import Any

from interfaces import DerivationSourceInterface


# Simulated derivation output for development
DEMO_DERIVATIONS: dict[str, dict[str, Any]] = {
    "/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv": {},
}


class MockDerivationSource(DerivationSourceInterface):
    """Mock implementation of DerivationSourceInterface."""

    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        """Return the demo derivation dict.

        Args:
            target: The derivation path (ignored; returns demo data).

        Returns:
            A dict mapping derivation paths to their metadata.
        """
        return DEMO_DERIVATIONS
