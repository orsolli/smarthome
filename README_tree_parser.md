# Tree Parser

A Python library for parsing and merging tree structures from Nix store listings.

## Dependency Tree

Below is a Mermaid diagram showing the dependency relationships between all functions in this project:

```mermaid
graph TD
    subgraph parser.py
        parse_tree_block[parse_tree_block]
        split_into_trees[split_into_trees]
        process_tree_output[process_tree_output]
        merge_nix_trees[merge_nix_trees]
    end

    subgraph merger.py
        merge_trees[merge_trees]
    end

    subgraph formatter.py
        generate_ascii_tree[generate_ascii_tree]
    end

    subgraph utils.py
        count_indent[count_indent]
        get_node_name[get_node_name]
    end

    subgraph main.py
        main[main]
    end

    subgraph __main__.py
        run_main[run_main]
    end

    %% parser.py dependencies
    parse_tree_block --> count_indent
    parse_tree_block --> get_node_name
    split_into_trees -.-> .
    
    %% process_tree_output dependencies
    process_tree_output --> split_into_trees
    process_tree_output --> parse_tree_block
    process_tree_output --> merge_trees
    process_tree_output --> generate_ascii_tree
    merge_nix_trees --> process_tree_output
    
    %% merger.py
    merge_trees -.-> .
    
    %% formatter.py
    generate_ascii_tree -.-> .
    
    %% utils.py
    count_indent -.-> .
    get_node_name -.-> .
    
    %% main.py
    main --> merge_nix_trees
    
    %% __main__.py
    run_main --> merge_nix_trees

    classDef parser_class fill:#e1f5fe,stroke:#01579b,stroke-width:2
    classDef merger_class fill:#fff3e0,stroke:#e65100,stroke-width:2
    classDef formatter_class fill:#e8f5e9,stroke:#1b5e20,stroke-width:2
    classDef utils_class fill:#f3e5f5,stroke:#4a148c,stroke-width:2
    classDef main_class fill:#ffebee,stroke:#c62828,stroke-width:2
    
    class parse_tree_block,split_into_trees,process_tree_output,merge_nix_trees parser_class
    class merge_trees merger_class
    class generate_ascii_tree formatter_class
    class count_indent,get_node_name utils_class
    class main main_class
    class run_main parser_class
```

## Usage

```python
from tree_parser.parser import merge_nix_trees

input_text = """/nix/store/root
└───/nix/store/child-a
    └───/nix/store/grandchild-a1"""

result = merge_nix_trees(input_text)
print(result['json'])
print(result['ascii'])
```

## Running Tests

```bash
python -m unittest test_complex_tree.py test_merge.py test_parser_wrapper.py
```
