{ pkgs ? import <nixpkgs> { } }:
with pkgs.python3Packages;
buildPythonApplication {
  pname = "read_han";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  buildInputs = [
    setuptools
  ];

  propagatedBuildInputs = [
    pyserial
  ];
}