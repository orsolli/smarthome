{ pkgs ? import <nixpkgs> { } }:
with pkgs.python3Packages;
buildPythonApplication {
  pname = "read_waveplus";
  version = "0.1";
  format = "pyproject";
  src = builtins.filterSource (
    name: type: (baseNameOf name == "app.py") || (baseNameOf name == "pyproject.toml")
  ) ./.;

  buildInputs = [
    setuptools
  ];

  propagatedBuildInputs = [
    bleak
  ];
}