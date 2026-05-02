from abc import ABC, abstractmethod
from interfaces.TreeNodeDict import TreeNodeDict

class TreeFormatterInterface(ABC):
    @abstractmethod
    def generate_ascii_tree(self, node: TreeNodeDict) -> str:
        pass
