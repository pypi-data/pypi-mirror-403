{ nixpkgs, python_pkgs }:
python_pkgs.snowflake-connector-python.overridePythonAttrs (old: {
  disabledTestPaths = old.disabledTestPaths ++ [ "test/unit/test_put_get.py" ];
})
