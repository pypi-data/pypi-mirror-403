path_filter: src:
path_filter {
  root = src;
  include = [
    "fluidattacks_batch_client"
    "tests"
    "pyproject.toml"
    "mypy.ini"
    "ruff.toml"
    "uv.lock"
  ];
}
