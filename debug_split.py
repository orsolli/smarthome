from tree_parser.parser import split_into_trees

input_text = """/nint/store/root
└───/nint/store/child-a
    └───/nint/store/grandchild-a1
/nint/store/root
└───/nint/store/child-a
    └───/nint/store/grandchild-a2
"""

trees = split_into_trees(input_text)
print(f"Number of trees: {len(trees)}")
for i, tree in enumerate(trees):
    print(f"Tree {i}:")
    for line in tree:
        print(f"  {line}")
