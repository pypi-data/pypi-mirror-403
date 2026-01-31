"""CLI subcommands for managing extensions."""

import importlib.util
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from paxx.cli.utils import check_project_context
from paxx.templates.ext import get_ext_dir, list_ext

app = typer.Typer(
    name="ext",
    help="Manage extensions (add-ons for existing infrastructure)",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def _load_install_module(ext_dir: Path):
    """Load the install module from an extension.

    Args:
        ext_dir: Path to the extension directory.

    Returns:
        The install module, or None if not found.
    """
    install_path = ext_dir / "install.py"
    if not install_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("install", install_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def _display_available_ext() -> None:
    """Display table of available extensions."""
    extensions = list_ext()

    if not extensions:
        console.print("[yellow]No extensions available yet.[/yellow]")
        return

    descriptions = {
        "arq": "Background task queue with ARQ (requires redis)",
        "websocket": "WebSocket connections with room support",
        "postgis": "PostGIS geospatial extension for Postgres",
    }

    table = Table(title="Available Extensions")
    table.add_column("Extension", style="cyan")
    table.add_column("Description", style="white")

    for name in extensions:
        description = descriptions.get(name, "No description available")
        table.add_row(name, description)

    console.print(table)
    console.print("\nUsage: [bold]paxx ext add <extension>[/bold]")


@app.command("add")
def add(
    name: str = typer.Argument(None, help="Name of the extension"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
) -> None:
    """Add an extension (arq, websocket, postgis, etc.).

    Extensions are add-ons that enhance existing infrastructure components.
    Unlike infrastructure components, they don't add new services but extend
    functionality of existing ones.

    Examples:
        paxx ext add arq         # Add ARQ task queue (requires redis)
        paxx ext add postgis     # Add PostGIS to postgres
        paxx ext list            # List available extensions
    """
    # If no name specified, show available extensions
    if name is None:
        console.print("[bright_red]Error:[/bright_red] Please specify an extension.\n")
        _display_available_ext()
        raise typer.Exit(1)

    # Validate we're in a project
    check_project_context()

    # Check if extension exists
    ext_dir = get_ext_dir(name)
    if not ext_dir:
        console.print(f"[bright_red]Error: Unknown extension '{name}'[/bright_red]\n")
        _display_available_ext()
        raise typer.Exit(1)

    console.print(f"Adding extension: [bold cyan]{name}[/bold cyan]")

    # Load and run the install module
    install_module = _load_install_module(ext_dir)
    if install_module is None or not hasattr(install_module, "install"):
        console.print(
            f"[bright_red]Error: No install.py found for '{name}'[/bright_red]"
        )
        raise typer.Exit(1)

    install_module.install(Path.cwd(), force=force)


@app.command("list")
def list_cmd() -> None:
    """List available extensions."""
    _display_available_ext()
