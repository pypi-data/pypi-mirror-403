{ nixpkgs, pynix, python_pkgs }:
let
  commit = "d7efeb417506f90ab2afadfc5db06ff8f553c04d"; # v2.4.1
  sha256 = "0vdnin2k1bwbp8x6ia08ji9zhiismb3c9714fm0zjgpwcd21x2z6";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/purity/-/archive/${commit}/purity-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
  extended_python_pkgs = python_pkgs // {
    inherit (bundle.deps) types-simplejson;
  };
in bundle.builders.pkgBuilder
(bundle.builders.requirements extended_python_pkgs)
