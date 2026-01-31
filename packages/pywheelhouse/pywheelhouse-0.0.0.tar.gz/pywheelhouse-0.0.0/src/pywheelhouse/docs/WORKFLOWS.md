# WORKFLOWS

Common workflows for building and installing wheelhouses.

## Local development install

Install open-source requirements first, then private packages in order:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml
```

If you want a lightweight install without dependencies:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --no-deps
```

## CI build (wheelhouse artifact)

Build wheels to a directory that can be published as an artifact:

```bash
python -m pywheelhouse --build --from-configuration wheelhouse.toml --wheelhouse-dir dist/wheelhouse
```

The output directory can be used as a wheelhouse artifact for downstream jobs.

## Offline install from wheelhouse

After building the wheelhouse, install from it using `--find-links`:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --wheelhouse-dir dist/wheelhouse --no-index
```

This pattern keeps pip from contacting the network during installs.
