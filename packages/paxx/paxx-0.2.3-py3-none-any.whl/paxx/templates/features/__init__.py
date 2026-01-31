"""paxx bundled features.

This module contains pre-built feature templates that can be scaffolded
into your project using the `paxx feature add` command.

Available features:
- auth: AWS Cognito authentication & user management
- example_products: Example CRUD feature for product catalog
- admin: Admin panel (coming soon)
- permissions: Role-based access control (coming soon)

Usage:
    uv run paxx feature add auth
    uv run paxx feature add example_products
"""

from pathlib import Path


def get_features_dir() -> Path:
    """Get the path to the bundled features directory."""
    return Path(__file__).parent


def get_feature_dir(feature_name: str) -> Path | None:
    """Get the path to a specific bundled feature directory.

    Args:
        feature_name: Name of the feature to get.

    Returns:
        Path to the feature directory, or None if not found.
    """
    feature_dir = get_features_dir() / feature_name
    if feature_dir.exists() and feature_dir.is_dir():
        return feature_dir
    return None


def list_available_features() -> list[str]:
    """List all available bundled features.

    Returns:
        List of feature names that can be added to a project.
    """
    features_dir = get_features_dir()
    features = []

    for item in features_dir.iterdir():
        # Skip __pycache__ and files
        if item.name.startswith("_") or item.name.startswith("."):
            continue
        if item.is_dir() and (item / "__init__.py").exists():
            features.append(item.name)

    return sorted(features)
