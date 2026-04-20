import sys
import os

# Add the project root to sys.path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from tree_parser import merge_nix_trees

def main():
    input_text = \"\"\"/nix/store/z35z9arr-nixos-command-example.drv
└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv
    └───/nix/store/xdgdrv000000000000000000000000000000-xdg-utils-9.99.0.drv
/nix/store/z35zarr-nixos-system-example-24.11.drv
└───/nix/store/etcdrv000000000000000000000000000000-etc.drv
    └───/nix/store/unitdrv0000000000000000000000000000-system-units.drv
\"\"\"

    result = merge_nix_trees(input_text)
    
    print(\"JSON representation:\")
    print(result['json'])
    print(\"\\n\\nASCII tree:\")
    print(result['ascii'])
    
    return result

if __name__ == \"__main__\":
    main()
