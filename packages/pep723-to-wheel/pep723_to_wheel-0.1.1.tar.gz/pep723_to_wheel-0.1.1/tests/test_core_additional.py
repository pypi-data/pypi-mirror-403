from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from pep723_to_wheel import core


def test_extract_pep723_block_handles_missing_block() -> None:
    assert core._extract_pep723_block("print('no header')") == ""
    assert core._parse_pep723_kv("") == {}


def test_pep723_header_renders_dependencies() -> None:
    header = core.Pep723Header(requires_python=None, dependencies=["requests>=2.0"])

    assert header.render_block() == "\n".join(
        [
            "# /// script",
            '# dependencies = ["requests>=2.0"]',
            "# ///",
        ]
    )


def test_pep723_header_omits_dependencies_when_empty() -> None:
    header = core.Pep723Header(requires_python=">=3.12", dependencies=[])

    assert header.render_block() == "\n".join(
        [
            "# /// script",
            '# requires-python = ">=3.12"',
            "# ///",
        ]
    )


def test_normalization_helpers_handle_edge_cases() -> None:
    assert core._normalize_project_name("My Script!") == "my-script"
    assert core._normalize_project_name("!!!") == "pep723-script"
    assert core._normalize_module_name("My Script!") == "my_script"
    assert core._normalize_module_name("123") == "pkg_123"


def test_format_dependencies_block_with_no_deps() -> None:
    assert core._format_dependencies_block([]) == ["dependencies = [", "]"]


def test_requires_helpers_parse_and_ignore_missing() -> None:
    metadata = "\n".join(
        [
            "Metadata-Version: 2.3",
            "Requires-Python: >=3.12",
            "Requires-Dist: requests>=2.0",
            "",
        ]
    )
    assert core._extract_requires_python(metadata) == ">=3.12"
    assert core._extract_requires_dist(metadata) == ["requests>=2.0"]
    assert core._extract_requires_python("Metadata-Version: 2.3\n") is None
    assert core._extract_requires_dist("Metadata-Version: 2.3\n") == []


def test_find_import_name_various_candidates(tmp_path: Path) -> None:
    wheel_path = tmp_path / "demo-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("my_package/__init__.py", "")
    with zipfile.ZipFile(wheel_path) as wheel:
        assert core._find_import_name(wheel, "My-Package") == "my_package"

    single_path = tmp_path / "single-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(single_path, "w") as wheel:
        wheel.writestr("solo.py", "")
    with zipfile.ZipFile(single_path) as wheel:
        assert core._find_import_name(wheel, "different") == "solo"

    multi_path = tmp_path / "multi-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(multi_path, "w") as wheel:
        wheel.writestr("alpha.py", "")
        wheel.writestr("beta.py", "")
    with zipfile.ZipFile(multi_path) as wheel:
        assert core._find_import_name(wheel, "multi") is None


def test_find_import_name_skips_reserved_paths(tmp_path: Path) -> None:
    wheel_path = tmp_path / "skip-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("pkg.dist-info/__init__.py", "")
        wheel.writestr("__pycache__/__init__.py", "")
        wheel.writestr("useful/__init__.py", "")
        wheel.writestr("folder/", "")
    with zipfile.ZipFile(wheel_path) as wheel:
        assert core._find_import_name(wheel, "useful") == "useful"


def test_build_script_from_metadata_errors(tmp_path: Path) -> None:
    missing_metadata = tmp_path / "missing-1.0.0-py3-none-any.whl"
    with zipfile.ZipFile(missing_metadata, "w") as wheel:
        wheel.writestr("package/__init__.py", "")

    with pytest.raises(ValueError, match="Wheel metadata not found"):
        core._build_script_from_metadata(missing_metadata)

    missing_name = tmp_path / "missing-name-1.0.0-py3-none-any.whl"
    metadata = "Metadata-Version: 2.3\nVersion: 1.0.0\n"
    with zipfile.ZipFile(missing_name, "w") as wheel:
        wheel.writestr("package/__init__.py", "")
        wheel.writestr("package-1.0.0.dist-info/METADATA", metadata)

    with pytest.raises(ValueError, match="Wheel metadata missing Name field"):
        core._build_script_from_metadata(missing_name)


def test_script_text_from_wheel_falls_back_to_metadata(tmp_path: Path) -> None:
    wheel_path = tmp_path / "sample-1.0.0-py3-none-any.whl"
    metadata = "\n".join(
        [
            "Metadata-Version: 2.3",
            "Name: Sample",
            "Version: 1.0.0",
            "",
        ]
    )
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("sample/__init__.py", "")
        wheel.writestr("sample-1.0.0.dist-info/METADATA", metadata)

    script_text = core._script_text_from_wheel(wheel_path)

    assert "# /// script" in script_text
    assert 'dependencies = ["Sample"]' in script_text
    assert "import sample" in script_text


def test_build_script_from_metadata_without_import_name(tmp_path: Path) -> None:
    wheel_path = tmp_path / "sample-1.0.0-py3-none-any.whl"
    metadata = "\n".join(
        [
            "Metadata-Version: 2.3",
            "Name: Sample",
            "Version: 1.0.0",
            "",
        ]
    )
    with zipfile.ZipFile(wheel_path, "w") as wheel:
        wheel.writestr("sample-1.0.0.dist-info/METADATA", metadata)

    script_text = core._build_script_from_metadata(wheel_path)

    assert "import sample" not in script_text


def test_download_wheel_selects_latest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wheel_v1 = tmp_path / "pkg-1.0.0-py3-none-any.whl"
    wheel_v2 = tmp_path / "pkg-2.0.0-py3-none-any.whl"
    wheel_v1.touch()
    wheel_v2.touch()

    monkeypatch.setattr(core.subprocess, "run", lambda *args, **kwargs: None)

    assert core._download_wheel("pkg", tmp_path) == wheel_v2


def test_download_wheel_raises_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core.subprocess, "run", lambda *args, **kwargs: None)

    with pytest.raises(FileNotFoundError, match="No wheel downloaded"):
        core._download_wheel("pkg", tmp_path)


def test_build_temp_project_errors_on_missing_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(core.subprocess, "run", lambda *args, **kwargs: None)

    with pytest.raises(FileNotFoundError, match="No wheel produced"):
        core._build_temp_project(script, tmp_path, version="1.0.0")


def test_build_script_to_wheel_raises_for_missing_script(tmp_path: Path) -> None:
    missing_script = tmp_path / "missing.py"

    with pytest.raises(FileNotFoundError):
        core.build_script_to_wheel(missing_script)


def test_build_temp_project_errors_on_multiple_wheels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = tmp_path / "script.py"
    script.write_text(
        "\n".join(
            [
                "# /// script",
                "# ///",
                "print('hello')",
                "",
            ]
        ),
        encoding="utf-8",
    )

    def fake_run(*args, **kwargs) -> None:
        cwd = Path(kwargs["cwd"])
        dist_dir = cwd / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        (dist_dir / "a.whl").touch()
        (dist_dir / "b.whl").touch()

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Expected exactly one wheel"):
        core._build_temp_project(script, tmp_path, version="1.0.0")


def test_import_wheel_to_script_downloads_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel_path = tmp_path / "sample-1.0.0-py3-none-any.whl"
    wheel_path.touch()

    monkeypatch.setattr(core, "_download_wheel", lambda *_: wheel_path)
    monkeypatch.setattr(core, "_script_text_from_wheel", lambda *_: "print('hi')\n")

    output_path = tmp_path / "out" / "script.py"
    result = core.import_wheel_to_script("sample", output_path)

    assert result.script_path == output_path
    assert output_path.read_text(encoding="utf-8") == "print('hi')\n"
