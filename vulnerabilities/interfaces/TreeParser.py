from abc import ABC, abstractmethod
from typing import List, Dict, Any
from interfaces.TreeNodeDict import TreeNodeDict

class TreeParserInterface(ABC):
    @abstractmethod
    def parse_tree_block(self, lines: List[str]) -> TreeNodeDict | None:
        pass

    @abstractmethod
    def split_into_trees(self, input_text: str) -> List[List[str]]:
        pass
