# CLI

pywheelhouse is a small CLI for building and installing wheelhouses using a
TOML configuration file.

## Basic usage

Install in dependency order:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml
```

Build wheels into a wheelhouse directory:

```bash
python -m pywheelhouse --build --from-configuration wheelhouse.toml
```

## Options

- `--install`: install requirements and private packages in order
- `--build`: build wheels into the wheelhouse directory
- `--from-configuration PATH`: configuration file (TOML)
- `--wheelhouse-dir PATH`: override the wheelhouse dir or `--find-links` path
- `--no-deps`: disable dependency installation for all pip operations
- `--pip-arg ARG`: extra pip argument (repeatable, applied last)
- `--ignore-invalid-pip-args`: ignore unknown/malformed pip args and warn
- `--version`: show version and exit

## Passing pip arguments

pywheelhouse forwards extra CLI arguments to pip. Examples:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --no-build-isolation
python -m pywheelhouse --install --from-configuration wheelhouse.toml --proxy ""
```

If a pip option conflicts with a pywheelhouse option name, use `--pip-arg`:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --pip-arg --no-index
```

Arguments from the command line are applied after config and per-package
`pip_args` (last-wins precedence).
