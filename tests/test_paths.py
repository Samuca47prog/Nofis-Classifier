from pathlib import Path

import pytest

from nofis_classifier.paths import find_project_root


def test_find_project_root_from_nested_directory(tmp_path: Path) -> None:
    marker = tmp_path / "pyproject.toml"
    marker.write_text("[project]\nname = \"example\"\n", encoding="utf-8")
    nested = tmp_path / "notebooks" / "scratch"
    nested.mkdir(parents=True)

    assert find_project_root(start=nested) == tmp_path


def test_find_project_root_raises_when_marker_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="pyproject.toml"):
        find_project_root(start=tmp_path)

