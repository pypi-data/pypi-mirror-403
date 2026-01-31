"""Extensions for paxx projects."""

from pathlib import Path


def get_ext_dir(name: str) -> Path | None:
    """Get path to an extension by name."""
    ext_dir = Path(__file__).parent / name
    if ext_dir.is_dir() and (ext_dir / "__init__.py").exists():
        return ext_dir
    return None


def list_ext() -> list[str]:
    """List all available extensions."""
    ext_root = Path(__file__).parent
    return [
        d.name
        for d in ext_root.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    ]
