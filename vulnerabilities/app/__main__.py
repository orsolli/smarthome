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
    input_text = """/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/dygnwmswkg1v839pnd3zg6b4431ggbg0-system-path.drv
    └───/nix/store/vy9hrd513j41b4vc4708vkmsv0q7ic3c-xdg-utils-1.2.1.drv
        └───/nix/store/np97p7m6vpav7r1v824pjck5v2p0xzci-resholve-0.10.7.drv
/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/mi5kw37r0ndvd9w7fr9s1y5f063xhv0v-etc.drv
    └───/nix/store/0ibyb85glxh980wmnr1i1i1hm0xclh7l-system-units.drv
/nix/store/z35z9cw932qg03bb0anvj0j9n0gr7idr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/dygnwmswkg1v839pnd3zg6b4431ggbg0-system-path.drv
    └───/nix/store/ydqg7di6cd4gvdfjv1c5hpmsjd2x7hdx-brave-1.88.138.drv
        └───/nix/store/hcydnrs0kr1sdj9mqz772vlp8qhp4cls-snappy-1.2.2.drv
"""

    result = merge_nix_trees(input_text)
    
    print("JSON representation:")
    print(result['json'])
    print("\n\nASCII tree:")
    print(result['ascii'])
    
    return result

if __name__ == "__main__":
    main()
