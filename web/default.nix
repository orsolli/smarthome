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

  postInstall = ''
    echo "#!${pkgs.stdenv.shell}" > $out/bin/start-server
    echo "exec ${pythonEnv.interpreter} -m gunicorn -w 1 -b 127.0.0.1:8000 app:app" >> $out/bin/start-server
    chmod +x $out/bin/start-server
  '';

}