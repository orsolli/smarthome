from abc import ABC, abstractmethod
from typing import Dict, Any

class TreeFormatterInterface(ABC):
    @abstractmethod
    def generate_ascii_tree(self, node: Dict[str, Any]) -> str:
        pass
