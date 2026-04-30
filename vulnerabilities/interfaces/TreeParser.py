from abc import ABC, abstractmethod
from typing import List, Dict, Any

class TreeParserInterface(ABC):
    @abstractmethod
    def parse_tree_block(self, lines: List[str]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def split_into_trees(self, input_text: str) -> List[List[str]]:
        pass
