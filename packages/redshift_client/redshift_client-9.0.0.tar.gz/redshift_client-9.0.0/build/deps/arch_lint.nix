{ nixpkgs, pynix, python_pkgs }:
let
  commit = "ff6578a129d8b7401844fca2a5ebbe1c1331d757"; # v4.0.3
  sha256 = "1qy3czqqjirl801p6ki11krydwr9yq984177xzn2bbk20xcdxvca";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/arch_lint/-/archive/${commit}/arch_lint-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // { inherit (bundle.deps) grimp; };
in bundle.builders.pkgBuilder
(bundle.builders.requirements extended_python_pkgs)
