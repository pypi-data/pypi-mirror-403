import os
from datetime import datetime
from pathlib import Path
import zipfile

from pep723_to_wheel import core


def test_build_and_import_round_trip(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                '# requires-python = ">=3.12"',
                '# dependencies = ["requests>=2.0"]',
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = core.build_script_to_wheel(script, tmp_path)

    assert result.wheel_path.name.endswith(".whl")
    assert result.wheel_path.exists()

    output_path = tmp_path / "reconstructed.py"
    import_result = core.import_wheel_to_script(str(result.wheel_path), output_path)

    assert import_result.script_path == output_path
    assert import_result.script_path.read_text(encoding="utf-8") == script.read_text(
        encoding="utf-8"
    )


def test_pep723_header_parsing_and_render(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                '# requires-python = ">=3.12"',
                '# dependencies = ["pydantic>=2.5", "httpx"]',
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    header = core.Pep723Header.from_script(script)

    assert header.requires_python == ">=3.12"
    assert header.dependencies == ["pydantic>=2.5", "httpx"]
    assert header.render_block() == "\n".join(
        [
            "# /// script",
            '# requires-python = ">=3.12"',
            '# dependencies = ["pydantic>=2.5", "httpx"]',
            "# ///",
        ]
    )


def test_pep723_header_allows_missing_requires_python(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                '# dependencies = ["pydantic>=2.5"]',
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    header = core.Pep723Header.from_script(script)

    assert header.requires_python is None
    assert header.dependencies == ["pydantic>=2.5"]
    assert header.render_block() == "\n".join(
        [
            "# /// script",
            '# dependencies = ["pydantic>=2.5"]',
            "# ///",
        ]
    )


def test_build_uses_specified_version(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                '# requires-python = ">=3.12"',
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = core.build_script_to_wheel(script, tmp_path, version="2024.12.25")

    assert "2024.12.25" in result.wheel_path.name


def test_build_defaults_to_mtime_calver(tmp_path: Path) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                '# requires-python = ">=3.12"',
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    fixed_timestamp = datetime(2024, 12, 25, 12, 34, 56, tzinfo=core.UTC).timestamp()
    os.utime(script, (fixed_timestamp, fixed_timestamp))

    result = core.build_script_to_wheel(script, tmp_path)

    assert "2024.12" in result.wheel_path.name
    assert str(int(fixed_timestamp)) in result.wheel_path.name


def test_build_script_from_metadata_prefers_package_name_as_dependency(
    tmp_path: Path,
) -> None:
    wheel_path = tmp_path / "sample-1.0.0-py3-none-any.whl"
    metadata = "\n".join(
        [
            "Metadata-Version: 2.3",
            "Name: My-Package",
            "Version: 1.0.0",
            "Requires-Python: >=3.12",
            "Requires-Dist: requests>=2.0",
            "",
        ]
    )
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("my_package/__init__.py", "")
        wheel.writestr("my_package-1.0.0.dist-info/METADATA", metadata)

    script_text = core._build_script_from_metadata(wheel_path)

    assert script_text == "\n".join(
        [
            "# /// script",
            '# requires-python = ">=3.12"',
            '# dependencies = ["My-Package", "requests>=2.0"]',
            "# ///",
            "import my_package",
            "",
        ]
    )


def test_import_uses_embedded_script_when_present(tmp_path: Path) -> None:
    wheel_path = tmp_path / "sample-1.0.0-py3-none-any.whl"
    script_contents = "\n".join(
        [
            "# /// script",
            '# requires-python = ">=3.12"',
            "# ///",
            "print('hello from wheel')",
            "",
        ]
    )
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("package/script.py", script_contents)
        wheel.writestr("package/__init__.py", "")
        wheel.writestr(
            "package-1.0.0.dist-info/METADATA",
            "Metadata-Version: 2.3\nName: package\nVersion: 1.0.0\n",
        )

    output_path = tmp_path / "imported.py"
    result = core.import_wheel_to_script(str(wheel_path), output_path)

    assert result.script_path.read_text(encoding="utf-8") == script_contents


def test_marimo_example_round_trip(tmp_path: Path) -> None:
    example_path = Path(__file__).parent / "examples" / "marimo_notebook.py"
    script_text = example_path.read_text(encoding="utf-8")
    script_path = tmp_path / "marimo_notebook.py"
    script_path.write_text(script_text, encoding="utf-8")

    build_result = core.build_script_to_wheel(script_path, tmp_path)

    output_path = tmp_path / "imported_marimo_notebook.py"
    import_result = core.import_wheel_to_script(
        str(build_result.wheel_path), output_path
    )

    assert import_result.script_path == output_path
    assert import_result.script_path.read_text(encoding="utf-8") == script_text
