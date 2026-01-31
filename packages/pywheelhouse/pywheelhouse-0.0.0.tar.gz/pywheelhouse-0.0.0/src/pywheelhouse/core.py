from __future__ import annotations

import re
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    pass


class PipError(RuntimeError):
    def __init__(self, message: str, returncode: int) -> None:
        super().__init__(message)
        self.returncode = returncode


@dataclass(frozen=True)
class PrivatePackage:
    name: str
    path: Path
    extras: tuple[str, ...]
    pip_args: tuple[str, ...]
    editable: bool = False

    def target(self) -> str:
        target = str(self.path)
        if self.extras:
            target = f"{target}[{','.join(self.extras)}]"
        return target


@dataclass(frozen=True)
class WheelhouseConfig:
    root_dir: Path
    requirements: tuple[str, ...]
    requirements_files: tuple[Path, ...]
    private_packages: tuple[PrivatePackage, ...]
    wheelhouse_dir: Path | None
    pip_args: tuple[str, ...]
    ignore_invalid_pip_args: bool


_PIP_OPTION_CACHE: dict[str, tuple[set[str], set[str]] | None] = {}


def load_config(path: Path) -> WheelhouseConfig:
    config_path = path.expanduser()
    if not config_path.exists():
        raise ConfigError(f"configuration file not found: {config_path}")

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    if not isinstance(data, dict):
        raise ConfigError("configuration file must contain a TOML table")

    root_dir = config_path.parent

    requirements = _read_str_list(data.get("requirements"), "requirements")
    requirements_files = [
        _resolve_path(root_dir, value)
        for value in _read_str_list(
            data.get("requirements_files"), "requirements_files"
        )
    ]

    wheelhouse = data.get("wheelhouse") or {}
    if not isinstance(wheelhouse, dict):
        raise ConfigError("wheelhouse must be a table")

    wheelhouse_dir_value = wheelhouse.get("output_dir") or wheelhouse.get(
        "wheelhouse_dir"
    )
    if wheelhouse_dir_value is not None and not isinstance(wheelhouse_dir_value, str):
        raise ConfigError("wheelhouse.output_dir must be a string")

    wheelhouse_dir = (
        _resolve_path(root_dir, wheelhouse_dir_value) if wheelhouse_dir_value else None
    )

    pip_args = _read_str_list(wheelhouse.get("pip_args"), "wheelhouse.pip_args")
    ignore_invalid_pip_args = wheelhouse.get("ignore_invalid_pip_args", False)
    if not isinstance(ignore_invalid_pip_args, bool):
        raise ConfigError("wheelhouse.ignore_invalid_pip_args must be a boolean")

    for req_file in requirements_files:
        if not req_file.exists():
            raise ConfigError(f"requirements file not found: {req_file}")

    private_entries = data.get("private", [])
    if not isinstance(private_entries, list):
        raise ConfigError("private must be an array of tables")

    private_packages: list[PrivatePackage] = []
    for idx, entry in enumerate(private_entries, start=1):
        if not isinstance(entry, dict):
            raise ConfigError(f"private[{idx}] must be a table")

        path_value = entry.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise ConfigError(f"private[{idx}].path is required")

        name = entry.get("name")
        if name is not None and not isinstance(name, str):
            raise ConfigError(f"private[{idx}].name must be a string")

        extras = _read_str_list(entry.get("extras"), f"private[{idx}].extras")
        pkg_pip_args = _read_str_list(entry.get("pip_args"), f"private[{idx}].pip_args")
        editable = bool(entry.get("editable", False))

        pkg_path = _resolve_path(root_dir, path_value)
        if not pkg_path.exists():
            raise ConfigError(f"private[{idx}].path not found: {pkg_path}")

        private_packages.append(
            PrivatePackage(
                name=name or pkg_path.name,
                path=pkg_path,
                extras=tuple(extras),
                pip_args=tuple(pkg_pip_args),
                editable=editable,
            )
        )

    if not requirements and not requirements_files and not private_packages:
        raise ConfigError("configuration has no requirements or private packages")

    return WheelhouseConfig(
        root_dir=root_dir,
        requirements=tuple(requirements),
        requirements_files=tuple(requirements_files),
        private_packages=tuple(private_packages),
        wheelhouse_dir=wheelhouse_dir,
        pip_args=tuple(pip_args),
        ignore_invalid_pip_args=ignore_invalid_pip_args,
    )


def run_install(
    config: WheelhouseConfig,
    pip_args: list[str],
    *,
    no_deps: bool,
    find_links: Path | None = None,
    ignore_invalid_pip_args: bool = False,
) -> None:
    base_args = _filter_pip_args(
        list(config.pip_args),
        command="install",
        ignore_invalid=ignore_invalid_pip_args,
        label="wheelhouse.pip_args",
    )
    cli_args = _filter_pip_args(
        list(pip_args),
        command="install",
        ignore_invalid=ignore_invalid_pip_args,
        label="cli pip args",
    )
    if find_links:
        base_args += ["--find-links", str(find_links)]

    if config.requirements or config.requirements_files:
        _run_pip(
            _pip_install_command(
                requirements=config.requirements,
                requirements_files=config.requirements_files,
                pip_args=base_args + cli_args,
                no_deps=no_deps,
            )
        )

    for pkg in config.private_packages:
        pkg_args = _filter_pip_args(
            list(pkg.pip_args),
            command="install",
            ignore_invalid=ignore_invalid_pip_args,
            label=f"private[{pkg.name}].pip_args",
        )
        _run_pip(
            _pip_install_command(
                requirements=(pkg.target(),),
                requirements_files=(),
                pip_args=base_args + pkg_args + cli_args,
                no_deps=no_deps,
                editable=pkg.editable,
            )
        )


def run_build(
    config: WheelhouseConfig,
    wheelhouse_dir: Path,
    pip_args: list[str],
    *,
    no_deps: bool,
    ignore_invalid_pip_args: bool = False,
) -> None:
    wheelhouse_dir.mkdir(parents=True, exist_ok=True)
    base_args = _filter_pip_args(
        list(config.pip_args),
        command="wheel",
        ignore_invalid=ignore_invalid_pip_args,
        label="wheelhouse.pip_args",
    )
    cli_args = _filter_pip_args(
        list(pip_args),
        command="wheel",
        ignore_invalid=ignore_invalid_pip_args,
        label="cli pip args",
    )

    if config.requirements or config.requirements_files:
        _run_pip(
            _pip_wheel_command(
                requirements=config.requirements,
                requirements_files=config.requirements_files,
                pip_args=base_args + cli_args,
                no_deps=no_deps,
                wheelhouse_dir=wheelhouse_dir,
                find_links=None,
            )
        )

    for pkg in config.private_packages:
        pkg_args = _filter_pip_args(
            list(pkg.pip_args),
            command="wheel",
            ignore_invalid=ignore_invalid_pip_args,
            label=f"private[{pkg.name}].pip_args",
        )
        _run_pip(
            _pip_wheel_command(
                requirements=(pkg.target(),),
                requirements_files=(),
                pip_args=base_args + pkg_args + cli_args,
                no_deps=no_deps,
                wheelhouse_dir=wheelhouse_dir,
                find_links=wheelhouse_dir,
            )
        )


def _pip_install_command(
    *,
    requirements: tuple[str, ...],
    requirements_files: tuple[Path, ...],
    pip_args: list[str],
    no_deps: bool,
    editable: bool = False,
) -> list[str]:
    command = _pip_base_command() + ["install"]
    if no_deps:
        command.append("--no-deps")
    command += pip_args
    for req_file in requirements_files:
        command += ["-r", str(req_file)]
    if editable:
        if len(requirements) != 1:
            raise ConfigError("editable installs require exactly one target")
        command += ["-e", requirements[0]]
    else:
        command += list(requirements)
    return command


def _pip_wheel_command(
    *,
    requirements: tuple[str, ...],
    requirements_files: tuple[Path, ...],
    pip_args: list[str],
    no_deps: bool,
    wheelhouse_dir: Path,
    find_links: Path | None,
) -> list[str]:
    command = _pip_base_command() + ["wheel", "--wheel-dir", str(wheelhouse_dir)]
    if no_deps:
        command.append("--no-deps")
    if find_links:
        command += ["--find-links", str(find_links)]
    command += pip_args
    for req_file in requirements_files:
        command += ["-r", str(req_file)]
    command += list(requirements)
    return command


def _pip_base_command() -> list[str]:
    return [sys.executable, "-m", "pip"]


def _run_pip(command: list[str]) -> None:
    print(f"+ {_format_command(command)}")
    result = subprocess.run(command)
    if result.returncode != 0:
        raise PipError("pip command failed", result.returncode)


def _format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _read_str_list(value: object, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{label} must be a list of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ConfigError(f"{label} must be a list of strings")
        item = item.strip()
        if item:
            result.append(item)
    return result


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path


def _filter_pip_args(
    args: list[str],
    *,
    command: str,
    ignore_invalid: bool,
    label: str,
) -> list[str]:
    if not ignore_invalid:
        return args

    option_info = _get_pip_option_info(command)
    if option_info is None:
        _warn(
            f"could not validate pip args for '{command}'; "
            "using provided arguments as-is"
        )
        return args

    allowed, requires_value = option_info
    result: list[str] = []
    idx = 0
    while idx < len(args):
        raw = args[idx]
        arg = raw.strip() if isinstance(raw, str) else ""
        if not arg:
            _warn(f"{label}: ignoring empty pip arg")
            idx += 1
            continue
        if arg in ("-", "--"):
            _warn(f"{label}: ignoring invalid pip arg '{raw}'")
            idx += 1
            continue
        if arg.startswith("--") and "=" in arg:
            key, _value = arg.split("=", 1)
            if key not in allowed:
                _warn(f"{label}: ignoring unknown pip option '{key}'")
                idx += 1
                continue
            result.append(arg)
            idx += 1
            continue
        if arg.startswith("-"):
            if arg not in allowed:
                _warn(f"{label}: ignoring unknown pip option '{arg}'")
                idx += 1
                continue
            if arg in requires_value:
                if idx + 1 >= len(args):
                    _warn(f"{label}: ignoring '{arg}' without a value")
                    idx += 1
                    continue
                value = args[idx + 1]
                if not isinstance(value, str):
                    _warn(f"{label}: ignoring '{arg}' without a value")
                    idx += 1
                    continue
                if value != "" and value.startswith("-"):
                    _warn(f"{label}: ignoring '{arg}' without a value")
                    idx += 1
                    continue
                result.append(arg)
                result.append(value)
                idx += 2
                continue
            result.append(arg)
            idx += 1
            continue

        _warn(f"{label}: ignoring non-option pip arg '{raw}'")
        idx += 1

    return result


def _get_pip_option_info(command: str) -> tuple[set[str], set[str]] | None:
    cached = _PIP_OPTION_CACHE.get(command)
    if cached is not None or command in _PIP_OPTION_CACHE:
        return cached

    result = subprocess.run(
        [sys.executable, "-m", "pip", command, "--help"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _PIP_OPTION_CACHE[command] = None
        return None

    allowed, requires_value = _parse_pip_help(result.stdout)
    _PIP_OPTION_CACHE[command] = (allowed, requires_value)
    return allowed, requires_value


def _parse_pip_help(help_text: str) -> tuple[set[str], set[str]]:
    allowed: set[str] = set()
    requires_value: set[str] = set()
    for line in help_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        parts = re.split(r"\s{2,}", stripped, maxsplit=1)
        option_part = parts[0]
        options = re.findall(r"(?<!\\S)(-\\w|--[\\w-]+)", option_part)
        if not options:
            continue
        for opt in options:
            allowed.add(opt)
        if "<" in option_part or "[" in option_part:
            for opt in options:
                requires_value.add(opt)
    return allowed, requires_value


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)
