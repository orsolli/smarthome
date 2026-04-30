from abc import ABC, abstractmethod
from typing import List, Dict, Any

class TreeMergerInterface(ABC):
    @abstractmethod
    def merge_trees(self, trees: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass
