# EXAMPLES

## Minimal configuration

```toml
requirements = ["requests>=2.31"]

[[private]]
path = "../packages/mock-private-a"
```

Install:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml
```

## Build then install from a wheelhouse

```toml
requirements = ["requests>=2.31"]

[wheelhouse]
output_dir = "dist/wheelhouse"

[[private]]
path = "../packages/mock-private-a"
```

Build:

```bash
python -m pywheelhouse --build --from-configuration wheelhouse.toml
```

Install from the wheelhouse:

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --wheelhouse-dir dist/wheelhouse --no-index
```

## Extra pip arguments

```bash
python -m pywheelhouse --install --from-configuration wheelhouse.toml --no-build-isolation --proxy ""
```
