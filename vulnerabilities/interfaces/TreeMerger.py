from abc import ABC, abstractmethod
from typing import List, Dict, Any, Sequence
from typing_extensions import TypedDict
from interfaces.TreeNodeDict import TreeNodeDict

class TreeMergerInterface(ABC):
    @abstractmethod
    def merge_trees(self, trees: List[TreeNodeDict]) -> TreeNodeDict | None:
        pass
