# CONFIG

The configuration file is TOML. Relative paths are resolved from the directory
containing the configuration file.

## Example

```toml
requirements = [
  "pandas>=2.2",
  "requests>=2.31",
]

requirements_files = [
  "requirements.txt",
]

[wheelhouse]
output_dir = "dist/wheelhouse"
pip_args = ["--index-url", "https://pypi.org/simple"]
ignore_invalid_pip_args = true

[[private]]
name = "mock-private-a"
path = "../packages/mock-private-a"
extras = ["fast"]
pip_args = ["--no-build-isolation"]

[[private]]
name = "mock-private-b"
path = "../packages/mock-private-b"
editable = true
```

## Top-level fields

- `requirements`: list of pip requirement specifiers installed first.
- `requirements_files`: list of requirements files installed first.
- `private`: ordered list of private package tables.

## [wheelhouse] table

- `output_dir`: default wheelhouse directory for `--build`.
- `wheelhouse_dir`: alias for `output_dir`.
- `pip_args`: list of pip args applied to all commands.
- `ignore_invalid_pip_args`: when true, drops unknown/malformed pip args.

## [[private]] entries

Each private entry is processed in order.

- `name`: display name for warnings and errors (optional).
- `path`: local path to the package (required).
- `extras`: list of extras, e.g. `["dev"]` (optional).
- `pip_args`: extra pip args for this package only (optional).
- `editable`: install with `-e` (optional, install mode only).
