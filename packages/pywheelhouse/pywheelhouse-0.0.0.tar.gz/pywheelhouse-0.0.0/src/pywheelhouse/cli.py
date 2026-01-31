from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .core import ConfigError, PipError, load_config, run_build, run_install


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build and install a local wheelhouse from a TOML configuration."
    )

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--install",
        action="store_true",
        help="Install requirements and private packages in order.",
    )
    action_group.add_argument(
        "--build",
        action="store_true",
        help="Build wheels into the wheelhouse directory.",
    )

    parser.add_argument(
        "--from-configuration",
        "--config",
        dest="config_path",
        required=True,
        help="Path to a TOML configuration file.",
    )
    parser.add_argument(
        "--wheelhouse-dir",
        dest="wheelhouse_dir",
        help="Override the wheelhouse output directory (or find-links path for installs).",
    )
    parser.add_argument(
        "--no-deps",
        action="store_true",
        help="Disable dependency installation for all pip operations.",
    )
    parser.add_argument(
        "--pip-arg",
        action="append",
        help="Extra pip argument to forward (repeatable, applied last).",
    )
    parser.add_argument(
        "--ignore-invalid-pip-args",
        action="store_true",
        help="Ignore unknown/malformed pip args and emit warnings.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pywheelhouse {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)

    pip_args: list[str] = []
    if args.pip_arg:
        pip_args.extend(args.pip_arg)
    pip_args.extend(extra)

    try:
        config = load_config(Path(args.config_path))
    except ConfigError as exc:
        print(f"error: {exc}")
        return 2

    ignore_invalid_pip_args = (
        args.ignore_invalid_pip_args or config.ignore_invalid_pip_args
    )

    wheelhouse_dir = None
    if args.wheelhouse_dir:
        wheelhouse_dir = Path(args.wheelhouse_dir).expanduser()
    elif config.wheelhouse_dir is not None:
        wheelhouse_dir = config.wheelhouse_dir

    try:
        if args.build:
            wheelhouse_dir = wheelhouse_dir or (config.root_dir / "wheelhouse")
            run_build(
                config,
                wheelhouse_dir=wheelhouse_dir,
                pip_args=pip_args,
                no_deps=args.no_deps,
                ignore_invalid_pip_args=ignore_invalid_pip_args,
            )
        else:
            run_install(
                config,
                pip_args=pip_args,
                no_deps=args.no_deps,
                find_links=wheelhouse_dir,
                ignore_invalid_pip_args=ignore_invalid_pip_args,
            )
    except ConfigError as exc:
        print(f"error: {exc}")
        return 2
    except PipError as exc:
        print(f"error: {exc}")
        return exc.returncode or 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
