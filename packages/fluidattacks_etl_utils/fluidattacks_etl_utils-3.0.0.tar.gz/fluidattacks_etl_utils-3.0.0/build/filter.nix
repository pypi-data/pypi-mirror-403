path_filter: src:
path_filter {
  root = src;
  include = [
    "fluidattacks_etl_utils"
    "tests"
    "pyproject.toml"
    "mypy.ini"
    "ruff.toml"
    "uv.lock"
  ];
}
