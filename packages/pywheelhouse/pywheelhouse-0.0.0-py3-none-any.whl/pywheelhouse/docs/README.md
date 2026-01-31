# pywheelhouse documentation

This documentation suite is bundled inside the installed package so it is
available offline.

## Access after installation

List available docs:

```bash
python -m pywheelhouse.docs --list
```

Print a document to stdout:

```bash
python -m pywheelhouse.docs --show CLI
```

Write all docs to a folder:

```bash
python -m pywheelhouse.docs --write-dir .\pywheelhouse-docs
```

## Document map

- CLI: command line usage and options
- CONFIG: configuration file format and fields
- WORKFLOWS: build and install patterns
- EXAMPLES: ready-to-run examples
- PYTHON: Python API usage
- LIMITATIONS: design tradeoffs and constraints
- SECURITY: privacy and data-handling notes
- TROUBLESHOOTING: common problems and fixes
- FAQ: common questions
- CHANGELOG: notable changes by release

## Overview

pywheelhouse builds and installs a local wheelhouse for private Python packages.
It reads a TOML configuration file that lists open-source requirements and
private package paths in the order they should be processed.

Key traits:

- Uses the local Python interpreter (`python -m pip`)
- Installs open-source requirements before private packages
- Builds wheels into a shared wheelhouse directory
- Forwards pip args from the config and command line
- Supports offline usage once a wheelhouse has been built
