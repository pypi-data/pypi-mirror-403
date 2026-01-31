"""Typer-based CLI entry points."""

from __future__ import annotations

from pathlib import Path

import typer

from pep723_to_wheel.core import build_script_to_wheel, import_wheel_to_script

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command("build")
def build_command(
    script_path: Path = typer.Argument(..., help="Path to the PEP 723 script."),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Directory for the built wheel."
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Wheel version (defaults to calendar versioning).",
    ),
) -> None:
    """Build a wheel from a PEP 723 script."""

    result = build_script_to_wheel(script_path, output_dir, version)
    typer.echo(str(result.wheel_path))


@app.command("import")
def import_command(
    wheel_or_package: str = typer.Argument(
        ..., help="Wheel path or package name to import."
    ),
    output_path: Path = typer.Option(
        ..., "--output", "-o", help="Path to write the reconstructed script."
    ),
) -> None:
    """Reconstruct a script from a wheel or package name."""

    result = import_wheel_to_script(wheel_or_package, output_path)
    typer.echo(str(result.script_path))
