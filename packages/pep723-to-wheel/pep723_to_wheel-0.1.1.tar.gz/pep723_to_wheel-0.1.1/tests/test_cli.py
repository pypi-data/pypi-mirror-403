from pathlib import Path

import pytest
from typer.testing import CliRunner

from pep723_to_wheel import cli
from pep723_to_wheel.core import BuildResult, ImportResult


def test_build_command_outputs_wheel_path(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    def fake_build(script_path: Path, output_dir: Path | None, version: str | None) -> BuildResult:
        assert script_path == Path("script.py")
        assert output_dir == Path("dist")
        assert version == "2024.01.01"
        return BuildResult(wheel_path=Path("dist/script-2024.01.01-py3-none-any.whl"))

    monkeypatch.setattr(cli, "build_script_to_wheel", fake_build)

    result = runner.invoke(
        cli.app,
        ["build", "script.py", "--output-dir", "dist", "--version", "2024.01.01"],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "dist/script-2024.01.01-py3-none-any.whl"


def test_import_command_outputs_script_path(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    def fake_import(wheel_or_package: str, output_path: Path) -> ImportResult:
        assert wheel_or_package == "pkg"
        assert output_path == Path("out.py")
        return ImportResult(script_path=Path("out.py"))

    monkeypatch.setattr(cli, "import_wheel_to_script", fake_import)

    result = runner.invoke(cli.app, ["import", "pkg", "--output", "out.py"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "out.py"
