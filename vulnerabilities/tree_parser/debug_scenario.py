from tree_parser.parser import parse_tree_block

def debug_scenario():
    input_text = """/nix/store/root
│   /nix/append/child-a
│   │   /nix/append/grandchild-a1
│   │   /nix/append/grandchild-a2
│   /nix/append/child-b
    /nix/other/sibling
"""
    lines = input_text.strip().split('\n')
    print("Starting parsing...")
    result = parse_tree_block(lines)
    print("Parsing complete.")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    debug_scenario()
