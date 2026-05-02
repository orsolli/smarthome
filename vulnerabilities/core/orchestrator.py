import json
from interfaces.TreeParser import TreeParserInterface
from interfaces.TreeMerger import TreeMergerInterface
from interfaces.TreeFormatter import TreeFormatterInterface
from interfaces.TreeOrchestrator import TreeOrchestratorInterface

class TreeOrchestrator(TreeOrchestratorInterface):
    def __init__(self, 
                 parser: TreeParserInterface, 
                 merger: TreeMergerInterface, 
                 formatter: TreeFormatterInterface):
        self.parser = parser
        self.merger = merger
        self.formatter = formatter

    def process_tree_output(self, input_text: str):
        tree_blocks = self.parser.split_into_trees(input_text)
        
        tree_dicts = []
        for tree_lines in tree_blocks:
            if tree_lines:
                tree = self.parser.parse_tree_block(tree_lines)
                if tree:
                    tree_dicts.append(tree)
        
        merged_tree = self.merger.merge_trees(tree_dicts)
        
        json_output = json.dumps(merged_tree, indent=2)
        ascii_output = self.formatter.generate_ascii_tree(merged_tree) if merged_tree else None
        
        return {
            'tree': merged_tree,
            'json': json_output,
            'ascii': ascii_output
        }
