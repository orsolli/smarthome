from typing import List, TypedDict

class TreeNodeDict(TypedDict):
    name: str
    pname: str
    drv_path: str
    children: List["TreeNodeDict"]
