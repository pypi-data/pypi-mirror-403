"""Infrastructure components for paxx projects."""

from pathlib import Path


def get_infra_dir(name: str) -> Path | None:
    """Get path to an infra component by name."""
    infra_dir = Path(__file__).parent / name
    if infra_dir.is_dir() and (infra_dir / "__init__.py").exists():
        return infra_dir
    return None


def list_infra() -> list[str]:
    """List all available infra components."""
    infra_root = Path(__file__).parent
    return [
        d.name
        for d in infra_root.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    ]
