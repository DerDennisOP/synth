{
  description = "MicroPython Raspberry Pico";
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    (flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
      };

      py = pkgs.python3.override { };

      pythonEnv = py.withPackages (ps: with ps; [
        distutils
        pip
        pkgutil-resolve-name
        setuptools
      ]);
    in {
      devShell = with pkgs; mkShell {
        packages = [
          mpremote
          thonny
          pythonEnv
        ];
      };
    }
  ));
}
