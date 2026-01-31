# FAQ

## Does pywheelhouse install dependencies?

Yes, by default it lets pip resolve and install dependencies. Use `--no-deps`
to disable dependency installation for all pip commands.

## What is the wheelhouse directory?

It is a directory that contains built wheel files. When `--wheelhouse-dir` is
used during installs, pywheelhouse passes it to pip as `--find-links`.

## Can I use editable installs?

Yes. Set `editable = true` on a `[[private]]` entry.

## Can I pass proxy or index args?

Yes. Add them in `[wheelhouse].pip_args`, per-package `pip_args`, or pass them
on the command line.
