from pathlib import Path


def find_project_root(marker: str = "pyproject.toml", start: Path | str | None = None) -> Path:
    """Return the nearest parent directory containing the project marker file."""
    current = Path(start).resolve() if start is not None else Path.cwd().resolve()

    for path in (current, *current.parents):
        if (path / marker).exists():
            return path

    raise FileNotFoundError(f"Nao encontrei {marker} a partir de {current}")

