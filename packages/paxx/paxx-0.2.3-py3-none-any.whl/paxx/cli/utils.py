"""Shared utilities for paxx CLI commands."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import typer
from jinja2 import Environment, FileSystemLoader
from rich.console import Console

console = Console()


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent.parent / "templates"


def to_snake_case(name: str) -> str:
    """Convert a string to snake_case.

    Args:
        name: The string to convert.

    Returns:
        The snake_case version of the string.
    """
    # Replace hyphens with underscores
    name = name.replace("-", "_")
    # Insert underscore before uppercase letters and convert to lowercase
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    # Remove any non-alphanumeric characters except underscores
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


def validate_name(name: str, entity_type: str = "name") -> str:
    """Validate and normalize a project or feature name.

    Args:
        name: The name to validate.
        entity_type: Type of entity for error messages (e.g., "Project", "Feature").

    Returns:
        The validated name.

    Raises:
        typer.BadParameter: If the name is invalid.
    """
    # Check it starts with a letter
    if not name[0].isalpha():
        raise typer.BadParameter(f"{entity_type} name must start with a letter")

    # Check for valid characters
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", name):
        raise typer.BadParameter(
            f"{entity_type} name can only contain letters, numbers, "
            "hyphens, and underscores"
        )

    return name


def create_jinja_env(templates_dir: Path | None = None) -> Environment:
    """Create a Jinja2 environment configured for paxx templates.

    Args:
        templates_dir: Path to templates directory. Defaults to paxx templates.

    Returns:
        Configured Jinja2 Environment.
    """
    if templates_dir is None:
        templates_dir = get_templates_dir()

    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        keep_trailing_newline=True,
    )


@dataclass
class ProjectContext:
    """Context information about a paxx project directory."""

    root: Path
    features_dir: Path
    deploy_dir: Path


def check_project_context(
    require_settings: bool = True,
) -> ProjectContext:
    """Check that we're in a paxx project directory.

    Args:
        require_settings: Whether to require settings.py.

    Returns:
        ProjectContext with paths to important directories.

    Raises:
        typer.Exit: If not in a valid project directory.
    """
    cwd = Path.cwd()

    # Check for key project files
    required_files = ["main.py"]
    if require_settings:
        required_files.append("settings.py")

    missing = [f for f in required_files if not (cwd / f).exists()]

    if missing:
        console.print(
            "[bright_red]Error: Not in a paxx project directory.\n"
            "Make sure you're running this command from your project root "
            "(where main.py and settings.py are located).[/bright_red]"
        )
        raise typer.Exit(1)

    # Ensure features directory exists
    features_dir = cwd / "features"
    if not features_dir.exists():
        features_dir.mkdir(parents=True)

    return ProjectContext(
        root=cwd,
        features_dir=features_dir,
        deploy_dir=cwd / "deploy",
    )


def check_required_file(filename: str, error_context: str = "project root") -> None:
    """Check that a required file exists in the current directory.

    Args:
        filename: Name of the file to check for.
        error_context: Context for the error message.

    Raises:
        typer.Exit: If the file doesn't exist.
    """
    if not Path(filename).exists():
        console.print(
            f"[bright_red]Error: {filename} not found in current directory.\n"
            f"Run this command from your {error_context}.[/bright_red]"
        )
        raise typer.Exit(1)


def run_command(
    cmd: list[str],
    *,
    check_file: str | None = None,
    error_context: str = "project root",
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command with standard error handling.

    Args:
        cmd: Command and arguments to run.
        check_file: If provided, verify this file exists before running.
        error_context: Context for error messages if check_file is missing.
        capture: Whether to capture output.

    Returns:
        The completed process.

    Raises:
        typer.Exit: If the command fails or required file is missing.
    """
    if check_file:
        check_required_file(check_file, error_context)

    result = subprocess.run(
        cmd,
        check=False,
        capture_output=capture,
        text=capture,
    )

    if result.returncode != 0:
        raise typer.Exit(result.returncode)

    return result
