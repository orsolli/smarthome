{ pkgs ? import <nixpkgs> { } }:
with pkgs.python3Packages;
buildPythonApplication {
  pname = "read_waveplus";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  buildInputs = [
    setuptools
  ];

  propagatedBuildInputs = [
    bluepy
    pandas
  ];
}