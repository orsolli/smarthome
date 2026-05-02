from typing import List, TypedDict

class TreeNodeDict(TypedDict):
    name: str
    children: List["TreeNodeDict"]
