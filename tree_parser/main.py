import json
from .parser import merge_nix_trees

def main():
    """Main function to demonstrate the merge functionality."""
    input_text = """/nix/store/z35z9arr-nixos-system-example-24.11.drv
└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv
    └───/nix/store/xdgdrv000000000000000000000000000000-xdg-utils-9.99.0.drv
        └───/nix/store/resdrv00000000000000000000000000000-resholve-9.99.0.drv
/nix/store/z35zarr-nixos-system-example-24.11.drv
└───/nix/store/etcdrv000000000000000000000000000000-etc.drv
    └───/nix/store/unitdrv0000000000000000000000000000-system-units.drv
/nix/store/z35zarr-nixos-system-Orjan_AMD-24.11.drv
└───/nix/store/pathdrv000000000000000000000000000000-system-path.drv
    └───/nix/store/bravedrv00000000000000000000000000-brave-9.99.0.drv
        └───/nix/store/snapdrv000000000000000000000000000-snappy-9.99.0.drv"""

    result = merge_nix_trees(input_text)
    
    print("JSON representation:")
    print(result['json'])
    print("\n\nASCII tree:")
    print(result['ascii'])
    
    return result

if __name__ == "__main__":
    main()
