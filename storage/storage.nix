{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "storage";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  nativeCheckInputs = [ pkgs.python3Packages.pytestCheckHook ];

  propagatedBuildInputs = with pkgs.python3Packages; [
    bottle
  ];

  buildInputs = with pkgs.python3Packages; [
    setuptools
  ];
}
