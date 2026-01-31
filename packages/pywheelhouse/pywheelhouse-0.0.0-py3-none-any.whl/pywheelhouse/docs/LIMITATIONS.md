# LIMITATIONS

- pywheelhouse does not compute a dependency graph. It installs in the order
  listed in the configuration file.
- Dependency resolution is delegated to pip unless `--no-deps` is used.
- It does not build or publish indices; it only calls pip to build wheels.
- Pip failures are surfaced directly; pywheelhouse does not retry or repair.
- The tool assumes local paths are valid Python packages (PEP 517/518).
