{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "vulnerabilities";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  nativeCheckInputs = [ pkgs.python3Packages.pytestCheckHook ];

  propagatedBuildInputs = with pkgs.python3Packages; [
    bottle
    setuptools
  ];
}
