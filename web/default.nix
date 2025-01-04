{ pkgs ? import <nixpkgs> { } }:
let
  pythonEnv = pkgs.python3.withPackages(ps: [
    ps.plotly
    ps.flask
    ps.gunicorn
    ps.setuptools
  ]);
in
pkgs.python3Packages.buildPythonApplication {
  pname = "timeseries_plot";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  propagatedBuildInputs = [
    pythonEnv
  ];
}