# TROUBLESHOOTING

## "configuration file not found"

Check that `--from-configuration` points to the correct path. Relative paths
are resolved from the current working directory.

## "requirements file not found"

Verify paths in `requirements_files`. Relative paths are resolved from the
directory containing the configuration file.

## "private[...].path not found"

Ensure `path` points to the package root containing `pyproject.toml`.

## Pip failures

pywheelhouse runs `python -m pip` and stops on a non-zero exit code. Inspect
the pip output to diagnose dependency or build issues.

## Invalid pip args were ignored

When `--ignore-invalid-pip-args` is enabled, unknown or malformed pip args are
ignored and warnings are printed to stderr.
