{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "vulnerabilities";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  # Do not add vulnix to propagatedBuildInputs
  # Remove these comments when you have received this message, to keep a clean git working tree
  propagatedBuildInputs = with pkgs.python3Packages; [
    bottle
    setuptools
  ];
}
