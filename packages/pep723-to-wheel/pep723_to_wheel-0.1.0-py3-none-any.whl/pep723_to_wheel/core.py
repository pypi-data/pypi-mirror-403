"""Core implementation for the pep723-to-wheel CLI."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import zipfile

from pydantic import BaseModel, ConfigDict, Field

PEP723_START = "# /// script"
PEP723_END = "# ///"
UTC = timezone.utc


@dataclass(frozen=True)
class BuildResult:
    """Result metadata for a build operation."""

    wheel_path: Path


@dataclass(frozen=True)
class ImportResult:
    """Result metadata for an import operation."""

    script_path: Path


class Pep723Header(BaseModel):
    """PEP 723 script metadata."""

    model_config = ConfigDict(populate_by_name=True)

    requires_python: str | None = Field(default=None, alias="requires-python")
    dependencies: list[str] = Field(default_factory=list)

    @classmethod
    def from_script(cls, script_path: Path) -> "Pep723Header":
        """Extract and parse a PEP 723 header from a script file."""

        text = script_path.read_text(encoding="utf-8")
        block = _extract_pep723_block(text)
        data = _parse_pep723_kv(block)
        return cls.model_validate(data)

    def render_block(self) -> str:
        """Render the PEP 723 header block."""

        body_lines: list[str] = []
        if self.requires_python:
            body_lines.append(f'requires-python = "{self.requires_python}"')
        if self.dependencies:
            deps_formatted = ", ".join(f'"{dep}"' for dep in self.dependencies)
            body_lines.append(f"dependencies = [{deps_formatted}]")
        return "\n".join(
            [
                PEP723_START,
                *[f"# {line}" for line in body_lines],
                PEP723_END,
            ]
        )


def _extract_pep723_block(text: str) -> str:
    lines = text.splitlines()
    inside_block = False
    block_lines: list[str] = []
    for line in lines:
        if line.strip() == PEP723_START:
            inside_block = True
            continue
        if line.strip() == PEP723_END and inside_block:
            break
        if inside_block:
            block_lines.append(line)
    return "\n".join(block_lines)


def _parse_pep723_kv(block: str) -> dict:
    if not block.strip():
        return {}
    cleaned = "\n".join(
        line.lstrip("#").lstrip() for line in block.splitlines()
    )
    return tomllib.loads(cleaned)


def _normalize_project_name(name: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return normalized or "pep723-script"


def _normalize_module_name(name: str) -> str:
    module_name = re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()
    if not module_name or module_name[0].isdigit():
        module_name = f"pkg_{module_name}"
    return module_name


def _format_dependencies_block(dependencies: list[str]) -> list[str]:
    lines = ["dependencies = ["]
    if dependencies:
        deps_formatted = ",\n    ".join(f"\"{dep}\"" for dep in dependencies)
        lines.append(f"    {deps_formatted}")
    lines.append("]")
    return lines


def _extract_requires_dist(metadata_text: str) -> list[str]:
    requirements: list[str] = []
    for line in metadata_text.splitlines():
        if line.startswith("Requires-Dist:"):
            requirements.append(line.replace("Requires-Dist:", "", 1).strip())
    return requirements


def _extract_requires_python(metadata_text: str) -> str | None:
    for line in metadata_text.splitlines():
        if line.startswith("Requires-Python:"):
            return line.replace("Requires-Python:", "", 1).strip()
    return None


def _calendar_version(script_path: Path) -> str:
    mtime = script_path.stat().st_mtime
    timestamp = datetime.fromtimestamp(mtime, tz=UTC)
    return f"{timestamp.year}.{timestamp.month:02d}.{int(mtime)}"


def _build_temp_project(
    script_path: Path,
    output_dir: Path,
    version: str,
) -> Path:
    pep723 = Pep723Header.from_script(script_path)
    dependencies = pep723.dependencies
    requires_python = pep723.requires_python

    project_name = _normalize_project_name(script_path.stem)
    module_name = _normalize_module_name(project_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / "src" / module_name
        package_dir.mkdir(parents=True)

        (package_dir / "__init__.py").write_text(
            f'"""Package for {project_name}."""\n',
            encoding="utf-8",
        )
        (package_dir / "script.py").write_text(
            script_path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        pyproject = temp_path / "pyproject.toml"
        toml_lines = [
            "[project]",
            f'name = "{project_name}"',
            f'version = "{version}"',
            'description = "PEP 723 script bundle"',
        ]
        if requires_python:
            toml_lines.append(f'requires-python = "{requires_python}"')
        toml_lines.extend(_format_dependencies_block(dependencies))
        toml_lines.extend(
            [
                "",
                "[build-system]",
                'requires = ["hatchling>=1.27.0"]',
                'build-backend = "hatchling.build"',
                "",
                "[tool.hatch.build.targets.wheel]",
                f'packages = ["src/{module_name}"]',
                "",
            ]
        )
        pyproject.write_text(
            "\n".join(toml_lines),
            encoding="utf-8",
        )

        temp_output_dir = temp_path / "dist"
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(temp_output_dir)],
            check=True,
            cwd=temp_path,
        )

        wheels = list(temp_output_dir.glob("*.whl"))
        if not wheels:
            raise FileNotFoundError(f"No wheel produced in {temp_output_dir}")
        if len(wheels) > 1:
            raise RuntimeError(
                f"Expected exactly one wheel in {temp_output_dir}, found {len(wheels)}: "
                f"{', '.join(str(w) for w in wheels)}"
            )
        output_dir.mkdir(parents=True, exist_ok=True)
        built_wheel = wheels[0]
        dest_wheel = output_dir / built_wheel.name
        shutil.copy2(built_wheel, dest_wheel)
        return dest_wheel


def _find_import_name(wheel: zipfile.ZipFile, package_name: str) -> str | None:
    normalized_package = package_name.replace("-", "_")
    candidates: set[str] = set()
    for name in wheel.namelist():
        if name.endswith("/"):
            continue
        parts = name.split("/")
        if len(parts) == 1 and name.endswith(".py"):
            candidates.add(Path(name).stem)
            continue
        if len(parts) >= 2 and parts[-1] == "__init__.py":
            top_level = parts[0]
            if top_level.endswith(".dist-info") or top_level.endswith(".data"):
                continue
            if top_level.startswith("__"):
                continue
            candidates.add(top_level)
    if normalized_package in candidates:
        return normalized_package
    if len(candidates) == 1:
        return next(iter(candidates))
    return None


def build_script_to_wheel(
    script_path: Path,
    output_dir: Path | None = None,
    version: str | None = None,
) -> BuildResult:
    """Build a wheel from a PEP 723 script.

    Args:
        script_path: Path to the PEP 723 script.
        output_dir: Directory to write the wheel into.

    Returns:
        BuildResult containing the wheel location.
    """

    if not script_path.exists():
        raise FileNotFoundError(script_path)
    target_dir = output_dir or script_path.parent / "dist"
    resolved_version = version or _calendar_version(script_path)
    wheel_path = _build_temp_project(script_path, target_dir, resolved_version)
    return BuildResult(wheel_path=wheel_path)


def _download_wheel(package: str, dest: Path) -> Path:
    subprocess.run(
        [
            "uv",
            "pip",
            "download",
            "--only-binary",
            ":all:",
            "--dest",
            str(dest),
            package,
        ],
        check=True,
    )
    wheels = sorted(dest.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No wheel downloaded for {package}")
    return wheels[-1]


def _read_script_from_wheel(wheel_path: Path) -> str | None:
    with zipfile.ZipFile(wheel_path) as wheel:
        for name in wheel.namelist():
            if name.endswith("/script.py"):
                return wheel.read(name).decode("utf-8")
    return None


def _build_script_from_metadata(wheel_path: Path) -> str:
    with zipfile.ZipFile(wheel_path) as wheel:
        metadata_name = next(
            (name for name in wheel.namelist() if name.endswith(".dist-info/METADATA")),
            None,
        )
        if metadata_name is None:
            raise ValueError("Wheel metadata not found.")
        metadata_text = wheel.read(metadata_name).decode("utf-8")
        name_line = next(
            (line for line in metadata_text.splitlines() if line.startswith("Name: ")),
            None,
        )
        if name_line is None:
            raise ValueError("Wheel metadata missing Name field.")
        package_name = name_line.replace("Name: ", "", 1).strip()
        import_name = _find_import_name(wheel, package_name)
    requires = _extract_requires_dist(metadata_text)
    requires_python = _extract_requires_python(metadata_text)
    all_packages = [package_name]
    all_packages.extend(dep for dep in requires if dep not in all_packages)
    header = Pep723Header(
        requires_python=requires_python,
        dependencies=all_packages,
    )
    lines = [header.render_block()]
    if import_name:
        lines.append(f"import {import_name}")
    lines.append("")
    return "\n".join(lines)


def _script_text_from_wheel(wheel_path: Path) -> str:
    script_text = _read_script_from_wheel(wheel_path)
    if script_text is None:
        script_text = _build_script_from_metadata(wheel_path)
    return script_text


def import_wheel_to_script(
    wheel_or_package: str,
    output_path: Path,
) -> ImportResult:
    """Reconstruct a script from a wheel or package name.

    Args:
        wheel_or_package: Wheel filename/path or a package name to install with uv.
        output_path: Destination path for the reconstructed script.

    Returns:
        ImportResult containing the script location.
    """

    wheel_path = Path(wheel_or_package)
    if wheel_path.exists():
        script_text = _script_text_from_wheel(wheel_path)
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            wheel_to_read = _download_wheel(wheel_or_package, temp_path)
            script_text = _script_text_from_wheel(wheel_to_read)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script_text, encoding="utf-8")
    return ImportResult(script_path=output_path)
