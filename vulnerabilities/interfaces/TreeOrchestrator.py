from abc import ABC, abstractmethod
from typing import Dict, Any

class TreeOrchestratorInterface(ABC):
    @abstractmethod
    def process_tree_output(self, input_text: str):
        pass
