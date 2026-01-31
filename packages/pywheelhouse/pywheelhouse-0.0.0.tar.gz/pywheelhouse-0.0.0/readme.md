# pywheelhouse

`pywheelhouse` is a small CLI for building and installing local wheelhouses for private
Python packages. It reads a TOML configuration that lists open-source requirements and
private package paths in the exact order they should be installed or built.

The CLI forwards any extra pip arguments so local installs can use flags like
`--no-build-isolation` or `--proxy` without extra wrappers.

## Install

```bash
pip install -e .
```

## Quick start

```bash
python -m pywheelhouse --install --from-configuration my_wheelhouse_config.toml --no-build-isolation
```

## Documentation (bundled)

Documentation ships inside the package so it is available offline:

```bash
python -m pywheelhouse.docs --list
python -m pywheelhouse.docs --show CLI
python -m pywheelhouse.docs --write-dir .\pywheelhouse-docs
```

## Configuration format (TOML)

Relative paths are resolved from the configuration file directory.

```toml
# Open source requirements (installed first)
requirements = [
  "pandas>=2.2",
  "requests>=2.31",
]

# Optional requirements files
requirements_files = [
  "requirements.txt",
]

[wheelhouse]
# Optional default output directory for --build
output_dir = "dist/wheelhouse"

# Optional global pip args applied to all commands
pip_args = ["--index-url", "https://pypi.org/simple"]

# Optional: ignore unknown/malformed pip args and warn
ignore_invalid_pip_args = true

[[private]]
name = "mock-private-a"
path = "../packages/mock-private-a"
extras = ["fast"]
pip_args = ["--no-build-isolation"]

[[private]]
name = "mock-private-b"
path = "../packages/mock-private-b"

[[private]]
name = "mock-private-c"
path = "../packages/mock-private-c"
```

## Build a wheelhouse

```bash
python -m pywheelhouse --build --from-configuration my_wheelhouse_config.toml
```

## Install in dependency order

```bash
python -m pywheelhouse --install --from-configuration my_wheelhouse_config.toml --no-deps
```

## CLI behavior

- `--install` installs open-source requirements first, then installs private packages in order.
- `--build` builds wheels into the wheelhouse directory (defaults to `wheelhouse/` next to the config).
- `--no-deps` disables dependency installation for all pip operations.
- Any extra CLI arguments (or `--pip-arg` entries) are forwarded to pip.
- CLI pip args are applied after config + per-package `pip_args` (last-wins precedence).
- `--ignore-invalid-pip-args` (or `wheelhouse.ignore_invalid_pip_args`) drops unknown/malformed pip args and prints warnings.

## Notes

- Build and install steps use the running Python interpreter (`python -m pip`).
- `[[private]]` entries are processed in order; later packages can depend on earlier ones.
