"""CLI subcommands for managing deployments."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from paxx.cli.utils import (
    check_project_context,
    create_jinja_env,
    get_templates_dir,
)

app = typer.Typer(
    name="deploy",
    help="Manage deployment configurations for your paxx project",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

console = Console()


def _get_deploys_templates_dir() -> Path:
    """Get the path to the deploys templates directory."""
    return get_templates_dir() / "deploys"


def _list_used_deployments(deploy_dir: Path) -> list[str]:
    """List deployment types currently in use (in deploy/ directory)."""
    if not deploy_dir.exists():
        return []

    return [
        d.name
        for d in deploy_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]


def _list_available_deployments() -> list[str]:
    """List available deployment types (from paxx templates)."""
    deploys_dir = _get_deploys_templates_dir()
    if not deploys_dir.exists():
        return []

    return [
        d.name
        for d in deploys_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]


def _display_deployments(used: list[str], available: list[str]) -> None:
    """Display tables of used and available deployments."""
    # Show used deployments
    if used:
        table = Table(title="Used Deployments (in deploy/)")
        table.add_column("Deployment Type", style="cyan")
        for name in sorted(used):
            table.add_row(name)
        console.print(table)
        console.print()

    # Show available deployments
    available_not_used = [d for d in available if d not in used]

    if available_not_used:
        table = Table(title="Available Deployments")
        table.add_column("Deployment Type", style="green")
        for name in sorted(available_not_used):
            table.add_row(name)
        console.print(table)
    elif available:
        console.print("[grey70]All available deployments are already in use.[/grey70]")
    else:
        console.print("[yellow]No deployment templates found.[/yellow]")

    console.print()
    console.print("Usage: [bold]paxx deploy add <deployment-type>[/bold]")


# Files to copy for linux-server deployment
# (relative paths in template dir -> output paths)
# The key is the template file name (without .jinja), value is the output path
LINUX_SERVER_FILES = {
    "deploy.sh": "deploy/linux-server/deploy.sh",
    "deploy-init.sh": "deploy/linux-server/deploy-init.sh",
    "deploy-if-changed.sh": "deploy/linux-server/deploy-if-changed.sh",
    "deploy-purge.sh": "deploy/linux-server/deploy-purge.sh",
    "get-status.sh": "deploy/linux-server/get-status.sh",
    "server-setup.sh": "deploy/linux-server/server-setup.sh",
    "docker-compose.yml": "deploy/linux-server/docker-compose.yml",
    "traefik-dynamic.yml": "deploy/linux-server/traefik-dynamic.yml",
    ".env.example": "deploy/linux-server/.env.example",
    "README.md": "deploy/linux-server/README.md",
    "build.yml.example": ".github/workflows/build.yml",
}

# Shell scripts that need execute permission
EXECUTABLE_FILES = [
    "deploy/linux-server/deploy.sh",
    "deploy/linux-server/deploy-init.sh",
    "deploy/linux-server/deploy-if-changed.sh",
    "deploy/linux-server/deploy-purge.sh",
    "deploy/linux-server/get-status.sh",
    "deploy/linux-server/server-setup.sh",
]


def _get_project_name(project_root: Path) -> str:
    """Get project name from settings.py or directory name."""
    settings_file = project_root / "settings.py"
    if settings_file.exists():
        content = settings_file.read_text()
        # Look for APP_NAME or similar pattern
        for line in content.split("\n"):
            if "APP_NAME" in line and "=" in line:
                # Extract quoted string value
                import re

                match = re.search(r'["\']([^"\']+)["\']', line)
                if match:
                    return match.group(1)
    # Fall back to directory name
    return project_root.name


@app.command("add")
def add(
    deployment_type: str = typer.Argument(
        None,
        help="Name of the deployment type to add (e.g., linux-server)",
    ),
) -> None:
    """Add a deployment configuration to your project.

    This command copies deployment templates from paxx to your project,
    setting up the necessary files and configurations for that deployment method.

    Examples:
        paxx deploy add linux-server    # Add linux server deployment
        paxx deploy add                 # List available deployments
    """
    # Get available deployments first (doesn't require project context)
    available = _list_available_deployments()

    # If no deployment type specified, show available options
    if deployment_type is None:
        console.print(
            "[bright_red]Error:[/bright_red] "
            "Please specify a deployment type to add.\n"
        )
        _display_deployments([], available)
        raise typer.Exit(1)

    # Now validate project context
    ctx = check_project_context()
    deploy_dir = ctx.deploy_dir

    # Check if deployment type exists
    deploys_dir = _get_deploys_templates_dir()
    deployment_template_dir = deploys_dir / deployment_type

    if not deployment_template_dir.exists():
        console.print(
            f"[bright_red]Error:[/bright_red] "
            f"Unknown deployment type '{deployment_type}'.\n"
        )
        if available:
            console.print("Available deployment types:")
            for d in sorted(available):
                console.print(f"  - {d}")
        else:
            console.print("[yellow]No deployment templates found.[/yellow]")
        raise typer.Exit(1)

    # Check for potential conflicts
    warnings = []
    workflow_file = ctx.root / ".github/workflows/build.yml"
    target_deploy_dir = deploy_dir / deployment_type

    if workflow_file.exists():
        warnings.append(
            "  - .github/workflows/build.yml already exists (will be overwritten)"
        )

    if target_deploy_dir.exists() and any(target_deploy_dir.iterdir()):
        warnings.append(
            f"  - deploy/{deployment_type}/ is not empty (files may be overwritten)"
        )

    # Ask for confirmation if there are warnings
    if warnings:
        console.print("[yellow]Warning:[/yellow]")
        for warning in warnings:
            console.print(warning)
        console.print()
        if not typer.confirm("Continue?"):
            console.print("[grey70]Aborted.[/grey70]")
            raise typer.Exit(0)

    console.print(
        f"Adding deployment configuration: [bold cyan]{deployment_type}[/bold cyan]\n"
    )

    # Get project context for template rendering
    project_name = _get_project_name(ctx.root)
    template_context = {
        "project_name": project_name,
        "project_name_snake": project_name.replace("-", "_"),
    }

    # Set up Jinja environment
    env = create_jinja_env()

    # Render and copy files
    try:
        files_mapping = LINUX_SERVER_FILES  # TODO: support other deployment types

        for template_name, output_path in files_mapping.items():
            template_file = f"deploys/{deployment_type}/{template_name}.jinja"
            full_output_path = ctx.root / output_path

            # Create parent directories
            full_output_path.parent.mkdir(parents=True, exist_ok=True)

            # Render template
            template = env.get_template(template_file)
            content = template.render(**template_context)
            full_output_path.write_text(content)

            console.print(f"  [green]Created[/green] {output_path}")

        # Create certs directory
        certs_dir = deploy_dir / deployment_type / "certs"
        certs_dir.mkdir(parents=True, exist_ok=True)
        console.print(
            f"  [green]Created[/green] deploy/{deployment_type}/certs/ "
            "(place TLS certs here)"
        )

        # Make scripts executable
        for script_path in EXECUTABLE_FILES:
            full_path = ctx.root / script_path
            if full_path.exists():
                full_path.chmod(full_path.stat().st_mode | 0o111)

        console.print()
        deployment_label = deployment_type.title().replace('-', ' ')
        console.print(f"[bold green]{deployment_label} deployment added![/bold green]")
        console.print()
        console.print("Next steps:")
        console.print(
            f"  1. Copy deploy/{deployment_type}/.env.example, rename to "
            f"deploy/{deployment_type}/.env and customize it."
        )
        console.print("  2. Push to GitHub the changes you want to deploy.")
        console.print(
            "  3. Create a git tag to trigger the build, eg.: "
            "git tag v1.0.0 && git push origin v1.0.0"
        )
        console.print(
            f"  4. Run: ./deploy/{deployment_type}/deploy-init.sh user@your-server"
        )

    except Exception as e:
        console.print(f"[bright_red]Error adding deployment: {e}[/bright_red]")
        raise typer.Exit(1) from None


@app.command("list")
def list_cmd() -> None:
    """List available deployment configurations."""
    available = _list_available_deployments()

    if not available:
        console.print("[yellow]No deployment templates available.[/yellow]")
        return

    table = Table(title="Available Deployments")
    table.add_column("Deployment Type", style="green")

    for name in sorted(available):
        table.add_row(name)

    console.print(table)
    console.print()
    console.print("Usage: [bold]paxx deploy add <deployment-type>[/bold]")
