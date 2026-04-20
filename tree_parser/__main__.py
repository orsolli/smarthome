import sys
import os

# Add the project root to sys.path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from tree_parser import merge_nix_trees

def main():
    input_text = \"\"\"/nix/store/z35z9arr-nixos-command-example.drv
└───/nix/store/dygnwmswkg1v839pnd3zg6b4431ggbg0-system-path.drv
    └───/nix/store/vy9hrd513j41b4vc4708vkmsv0q7ic3c-xdg-utils-1.2.1.drv
/nix/store/z35zarr-nixos-system-OrjanAMD-595.58.03-26.05pre977467.4c1018dae018.drv
└───/nix/store/mi5kw37r0ndvd9w7fr9s1y5f063xhv0v-etc.drv
    └───/nix/store/0ibyb85glxh980wmnr1i1i1hm0xclh7l-system-units.drv
\"\"\"

    result = merge_nix_trees(input_text)
    
    print(\"JSON representation:\")
    print(result['json'])
    print(\"\\n\\nASCII tree:\")
    print(result['ascii'])
    
    return result

if __name__ == \"__main__\":
    main()
