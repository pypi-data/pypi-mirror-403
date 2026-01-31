from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pywheelhouse.core import ConfigError, load_config, run_build, run_install


def _write_config(base: Path) -> Path:
    (base / "requirements.txt").write_text("requests>=2.31\n", encoding="utf-8")
    (base / "pkga").mkdir()
    (base / "pkgb").mkdir()

    config_text = """
requirements = [
  "pandas>=2.2",
]

requirements_files = [
  "requirements.txt",
]

[wheelhouse]
output_dir = "dist/wheelhouse"
pip_args = ["--index-url", "https://pypi.org/simple"]

[[private]]
name = "mock-a"
path = "pkga"
extras = ["extra1"]
pip_args = ["--no-build-isolation"]

[[private]]
name = "mock-b"
path = "pkgb"
editable = true
""".lstrip()

    config_path = base / "wheelhouse.toml"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path


def test_load_config_parses_values(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)

    config = load_config(config_path)

    assert config.root_dir == tmp_path
    assert config.requirements == ("pandas>=2.2",)
    assert config.requirements_files == (tmp_path / "requirements.txt",)
    assert config.wheelhouse_dir == tmp_path / "dist" / "wheelhouse"
    assert config.pip_args == ("--index-url", "https://pypi.org/simple")
    assert config.ignore_invalid_pip_args is False
    assert len(config.private_packages) == 2

    first = config.private_packages[0]
    assert first.name == "mock-a"
    assert first.path == tmp_path / "pkga"
    assert first.extras == ("extra1",)
    assert first.pip_args == ("--no-build-isolation",)
    assert first.editable is False

    second = config.private_packages[1]
    assert second.name == "mock-b"
    assert second.path == tmp_path / "pkgb"
    assert second.editable is True


def test_load_config_missing_requirements_file(tmp_path: Path) -> None:
    config_text = """
requirements_files = ["missing.txt"]
""".lstrip()
    config_path = tmp_path / "wheelhouse.toml"
    config_path.write_text(config_text, encoding="utf-8")

    with pytest.raises(ConfigError, match="requirements file not found"):
        load_config(config_path)


def test_run_install_builds_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_config(tmp_path)
    config = load_config(config_path)

    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> object:
        commands.append(command)
        return type("Result", (), {"returncode": 0})()

    import pywheelhouse.core as core

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    run_install(
        config,
        pip_args=["--proxy", ""],
        no_deps=True,
        find_links=tmp_path / "wheelhouse",
    )

    assert len(commands) == 3

    base = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-deps",
        "--index-url",
        "https://pypi.org/simple",
        "--find-links",
        str(tmp_path / "wheelhouse"),
    ]

    assert commands[0] == base + [
        "--proxy",
        "",
        "-r",
        str(tmp_path / "requirements.txt"),
        "pandas>=2.2",
    ]

    assert commands[1] == base + [
        "--no-build-isolation",
        "--proxy",
        "",
        f"{tmp_path / 'pkga'}[extra1]",
    ]

    assert commands[2] == base + [
        "--proxy",
        "",
        "-e",
        str(tmp_path / "pkgb"),
    ]


def test_run_build_builds_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = _write_config(tmp_path)
    config = load_config(config_path)

    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> object:
        commands.append(command)
        return type("Result", (), {"returncode": 0})()

    import pywheelhouse.core as core

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    wheelhouse_dir = tmp_path / "wheelhouse"
    run_build(
        config,
        wheelhouse_dir=wheelhouse_dir,
        pip_args=["--proxy", ""],
        no_deps=False,
    )

    assert len(commands) == 3

    base = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--wheel-dir",
        str(wheelhouse_dir),
    ]

    assert commands[0] == base + [
        "--index-url",
        "https://pypi.org/simple",
        "--proxy",
        "",
        "-r",
        str(tmp_path / "requirements.txt"),
        "pandas>=2.2",
    ]

    assert commands[1] == base + [
        "--find-links",
        str(wheelhouse_dir),
        "--index-url",
        "https://pypi.org/simple",
        "--no-build-isolation",
        "--proxy",
        "",
        f"{tmp_path / 'pkga'}[extra1]",
    ]

    assert commands[2] == base + [
        "--find-links",
        str(wheelhouse_dir),
        "--index-url",
        "https://pypi.org/simple",
        "--proxy",
        "",
        f"{tmp_path / 'pkgb'}",
    ]


def test_ignore_invalid_pip_args_warns_and_filters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "pkga").mkdir()
    config_text = """
requirements = [
  "pandas>=2.2",
]

[wheelhouse]
pip_args = ["--index-url", "https://pypi.org/simple", "--bogus"]
ignore_invalid_pip_args = true

[[private]]
name = "mock-a"
path = "pkga"
pip_args = ["--proxy"]
""".lstrip()

    config_path = tmp_path / "wheelhouse.toml"
    config_path.write_text(config_text, encoding="utf-8")
    config = load_config(config_path)

    commands: list[list[str]] = []

    def fake_run(command: list[str]) -> object:
        commands.append(command)
        return type("Result", (), {"returncode": 0})()

    import pywheelhouse.core as core

    monkeypatch.setattr(core.subprocess, "run", fake_run)
    monkeypatch.setattr(
        core,
        "_get_pip_option_info",
        lambda _command: (
            {"--index-url", "--proxy", "--trusted-host"},
            {"--index-url", "--proxy", "--trusted-host"},
        ),
    )

    run_install(
        config,
        pip_args=["--trusted-host", "pypi.org", "--unknown"],
        no_deps=False,
        ignore_invalid_pip_args=True,
    )

    assert len(commands) == 2
    assert commands[0] == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--index-url",
        "https://pypi.org/simple",
        "--trusted-host",
        "pypi.org",
        "pandas>=2.2",
    ]
    assert commands[1] == [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--index-url",
        "https://pypi.org/simple",
        "--trusted-host",
        "pypi.org",
        str(tmp_path / "pkga"),
    ]

    stderr = capsys.readouterr().err
    assert "--bogus" in stderr
    assert "--unknown" in stderr
    assert "--proxy" in stderr
