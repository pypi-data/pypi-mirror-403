{ nixpkgs, pynix, }:
let
  layer_1 = python_pkgs:
    python_pkgs // {
      arch-lint = import ./arch_lint.nix { inherit nixpkgs pynix python_pkgs; };
      s3transfer = python_pkgs.s3transfer.overridePythonAttrs (oldAttrs: {
        preCheck = nixpkgs.lib.optionalString nixpkgs.stdenv.isDarwin ''
          export TMPDIR="/tmp"
        '';
      });
    };
  layer_2 = python_pkgs:
    python_pkgs // {
      fa-purity = import ./fa_purity.nix { inherit nixpkgs pynix python_pkgs; };
      boto3 = pynix.overrideUtils.deepPkgOverride python_pkgs.s3transfer
        python_pkgs.boto3;
    };
  layer_3 = python_pkgs:
    python_pkgs // {
      redshift-client = let
        pkg =
          import ./redshift_client.nix { inherit nixpkgs pynix python_pkgs; };
      in pynix.overrideUtils.deepPkgOverride python_pkgs.s3transfer pkg;
      snowflake-connector-python = let
        pkg = import ./snowflake_connector_python.nix {
          inherit nixpkgs python_pkgs;
        };
      in pynix.overrideUtils.deepPkgOverride python_pkgs.s3transfer pkg;
    };
  python_pkgs =
    pynix.utils.compose [ layer_3 layer_2 layer_1 ] pynix.lib.pythonPackages;
in { inherit python_pkgs; }
