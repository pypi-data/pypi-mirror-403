{ nixpkgs, pynix, python_pkgs }:
let
  commit = "d6e517fc7d1604a3cb2a96b673b37e24311b114c"; # v9.0.0
  sha256 = "1viiqvraslfarv00m63hbxcdwjmmkn64i2lql9lm8yp0k5lla2rp";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/redshift_client/-/archive/${commit}/redshift_client-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
in bundle.builders.pkgBuilder (bundle.builders.requirements python_pkgs)
