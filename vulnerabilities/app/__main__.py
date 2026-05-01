import sys
import os

from typing import Dict, Any
from interfaces import (
    TreeParserInterface,
    TreeMergerInterface,
    TreeFormatterInterface,
    TreeOrchestratorInterface
)
from core.parser import TreeParserImpl
from core.merger import TreeMergerImpl
from core.formatter import TreeFormatterImpl
from core.orchestrator import TreeOrchestrator
import json

def get_tree_parser_orchestrator() -> TreeOrchestratorInterface:
    parser = TreeParserImpl()
    merger = TreeMergerImpl()
    formatter = TreeFormatterImpl()
    return TreeOrchestrator(parser, merger, formatter)

def merge_nix_trees(input_text: str) -> Dict[str, Any]:
    orchestrator = get_tree_parser_orchestrator()
    return orchestrator.process_tree_output(input_text)

def main():
    input_text = """/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv
    └───/nix/store/xdgdrv000000000000000000000000000000-xdg-utils-9.99.0.drv
        └───/nix/store/resdrv00000000000000000000000000000-resholve-9.99.0.drv
/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
└───/nix/store/etcdrv000000000000000000000000000000-etc.drv
    └───/nix/store/unitdrv0000000000000000000000000000-system-units.drv
/nix/store/sysdrv000000000000000000000000000000-nixos-system-example-24.11.drv
└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv
    └───/nix/store/bravedrv00000000000000000000000000-brave-9.99.0.drv
        └───/nix/store/snapdrv000000000000000000000000000-snappy-9.99.0.drv
"""

    result = merge_nix_trees(input_text)
    
    print("JSON representation:")
    print(result['json'])
    print("\n\nASCII tree:")
    print(result['ascii'])
    
    return result

if __name__ == "__main__":
    main()
