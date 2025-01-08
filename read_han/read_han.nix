{ pkgs ? import <nixpkgs> { } }:
with pkgs.python3Packages;
buildPythonApplication {
  pname = "read_han";
  version = "0.1";
  format = "pyproject";
  src = builtins.filterSource (
    name: type: (baseNameOf name == "app.py") || (baseNameOf name == "pyproject.toml")
  ) ./.;

  buildInputs = [
    setuptools
  ];

  propagatedBuildInputs = [
    pyserial
  ];
}