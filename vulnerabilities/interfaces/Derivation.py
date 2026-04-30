from abc import ABC, abstractmethod
from typing import Any


class DerivationSourceInterface(ABC):
    """Resolves a target path to its Nix derivation.

    Usage:
        source = DerivationSourceImpl()
        derivations = source.show_derivation("/run/current-system")
    """

    @abstractmethod
    def show_derivation(self, target: str) -> dict[str, dict[str, Any]]:
        """Resolve target to its derivation dict.

        Args:
            target: The derivation path to resolve (e.g. /run/current-system).

        Returns:
            A dict mapping derivation paths to their metadata.
        """
        ...

