# PYTHON

pywheelhouse also exposes a small Python API for programmatic usage.

## Load configuration

```python
from pathlib import Path
from pywheelhouse.core import load_config

config = load_config(Path("wheelhouse.toml"))
```

## Install in order

```python
from pywheelhouse.core import run_install

run_install(
    config,
    pip_args=["--no-build-isolation"],
    no_deps=False,
)
```

## Build a wheelhouse

```python
from pathlib import Path
from pywheelhouse.core import run_build

run_build(
    config,
    wheelhouse_dir=Path("dist/wheelhouse"),
    pip_args=[],
    no_deps=False,
)
```
