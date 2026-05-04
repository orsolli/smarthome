{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "vulnerabilities";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  propagatedBuildInputs = with pkgs.python3Packages; [
    bottle
    vulnix
  ];
}
