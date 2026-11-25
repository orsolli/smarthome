{ pkgs ? import <nixpkgs> { } }:
pkgs.python3Packages.buildPythonApplication {
  pname = "vulnerabilities";
  version = "0.1";
  format = "pyproject";
  src = ./.;

  nativeCheckInputs = [ pkgs.python3Packages.pytestCheckHook ];

  # The CLI shells out to `nix` and `vulnix`, so they are propagated: the
  # python wrapper builds the executable's PATH from these inputs, and they
  # end up in the service's closure.
  propagatedBuildInputs = with pkgs.python3Packages; [
    bottle
    setuptools
    pkgs.nix
    pkgs.vulnix
  ];
}
