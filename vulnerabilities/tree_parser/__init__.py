from typing import Dict, Any
from .interfaces import (
    TreeParserInterface,
    TreeMergerInterface,
    TreeFormatterInterface,
    TreeOrchestratorInterface
)
from .core.parser import TreeParserImpl
from .core.merger import TreeMergerImpl
from .core.formatter import TreeFormatterImpl
from .core.orchestrator import TreeOrchestrator
import json

def get_tree_parser_orchestrator() -> TreeOrchestratorInterface:
    parser = TreeParserImpl()
    merger = TreeMergerImpl()
    formatter = TreeFormatterImpl()
    return TreeOrchestrator(parser, merger, formatter)

def merge_nix_trees(input_text: str) -> Dict[str, Any]:
    orchestrator = get_tree_parser_orchestrator()
    return orchestrator.merge_nix_trees(input_text)
