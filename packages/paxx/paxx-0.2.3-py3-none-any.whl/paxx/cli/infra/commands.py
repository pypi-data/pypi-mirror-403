"""CLI subcommands for managing infrastructure components."""

import importlib.util
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from paxx.cli.utils import check_project_context
from paxx.templates.infra import get_infra_dir, list_infra

app = typer.Typer(
    name="infra",
    help="Manage infrastructure components",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def _load_install_module(infra_dir: Path):
    """Load the install module from an infra component.

    Args:
        infra_dir: Path to the infra component directory.

    Returns:
        The install module, or None if not found.
    """
    install_path = infra_dir / "install.py"
    if not install_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("install", install_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def _display_available_infra() -> None:
    """Display table of available infrastructure components."""
    infra = list_infra()

    if not infra:
        console.print("[yellow]No infrastructure components available yet.[/yellow]")
        return

    descriptions = {
        "redis": "Redis caching with async support",
        "storage": "Object storage (S3/MinIO)",
        "metrics": "Prometheus metrics and OpenTelemetry tracing",
    }

    table = Table(title="Available Infrastructure")
    table.add_column("Component", style="cyan")
    table.add_column("Description", style="white")

    for name in infra:
        description = descriptions.get(name, "No description available")
        table.add_row(name, description)

    console.print(table)
    console.print("\nUsage: [bold]paxx infra add <component>[/bold]")


@app.command("add")
def add(
    name: str = typer.Argument(None, help="Name of the infrastructure component"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
) -> None:
    """Add an infrastructure component (redis, tasks, storage, etc.).

    Infrastructure components modify core files, docker-compose, and dependencies.
    Unlike domain features, they integrate with your project's foundation.

    Examples:
        paxx infra add redis     # Add Redis caching
        paxx infra list          # List available components
    """
    # If no name specified, show available components
    if name is None:
        console.print(
            "[bright_red]Error:[/bright_red] "
            "Please specify an infrastructure component.\n"
        )
        _display_available_infra()
        raise typer.Exit(1)

    # Validate we're in a project
    check_project_context()

    # Check if infra exists
    infra_dir = get_infra_dir(name)
    if not infra_dir:
        console.print(
            f"[bright_red]Error: Unknown infra component '{name}'[/bright_red]\n"
        )
        _display_available_infra()
        raise typer.Exit(1)

    console.print(f"Adding infrastructure: [bold cyan]{name}[/bold cyan]")

    # Load and run the install module
    install_module = _load_install_module(infra_dir)
    if install_module is None or not hasattr(install_module, "install"):
        console.print(
            f"[bright_red]Error: No install.py found for '{name}'[/bright_red]"
        )
        raise typer.Exit(1)

    install_module.install(Path.cwd(), force=force)


@app.command("list")
def list_cmd() -> None:
    """List available infrastructure components."""
    _display_available_infra()
