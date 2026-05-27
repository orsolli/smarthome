{ pkgs ? import <nixpkgs> { } }:
pkgs.python314Packages.buildPythonApplication {
  pname = "storage";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  nativeCheckInputs = [ pkgs.python314Packages.pytestCheckHook ];

  propagatedBuildInputs = with pkgs.python314Packages; [
    bottle
    psutil
  ];

  buildInputs = with pkgs.python314Packages; [
    setuptools
  ];
}
