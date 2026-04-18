from .parser import merge_nix_trees

def run_main():
    """Run the main function with dummy input."""
    input_text = """/nint/store/root
└───/nint/store/child-a
    └───/nint/store/grandchild-a1
/nint/store/root
└───/nint/store/child-a
    └───/nint/store/grandchild-a2
"""
    return merge_nix_trees(input_text)

if __name__ == "__main__":
    import json
    result = run_main()
    print(json.dumps(result['tree'], indent=2))
