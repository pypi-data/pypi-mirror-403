"""Installation script for ARQ extension."""

from pathlib import Path

from rich.console import Console

from paxx.templates.installer import TemplateInstaller

console = Console()


def _check_redis_configured(project_path: Path) -> bool:
    """Check if Redis is configured in the project.

    Args:
        project_path: Path to the project root.

    Returns:
        True if redis_url is found in settings.py.
    """
    settings_path = project_path / "settings.py"
    if settings_path.exists():
        settings_content = settings_path.read_text()
        return "redis_url" in settings_content.lower()
    return False


def install(project_path: Path, force: bool = False) -> None:
    """Install ARQ extension.

    Args:
        project_path: Path to the project root.
        force: Whether to overwrite existing files.
    """
    installer = TemplateInstaller(project_path)
    component_dir = Path(__file__).parent

    # Check prerequisites - ARQ requires Redis
    if not _check_redis_configured(project_path):
        console.print(
            "[yellow]Note:[/yellow] ARQ requires Redis. "
            "Run [bold]paxx infra add redis[/bold] or configure ARQ_REDIS_URL."
        )

    # Copy templates to services/
    installer.copy_templates(component_dir / "templates", project_path / "services")

    # Add dependencies
    installer.add_dependencies(component_dir / "dependencies.txt")

    # Add env vars
    installer.add_env_vars_from_file(component_dir / "env.json")

    # Print success and next steps
    installer.print_success("arq")
    installer.print_next_steps()

    # ARQ-specific usage instructions
    console.print()
    console.print("[bold]Running the worker:[/bold]")
    console.print("  [grey70]uv run arq services.tasks.WorkerSettings[/grey70]")
    console.print()
    console.print("[bold]Enqueue tasks from your code:[/bold]")
    console.print("  [grey70]from services.arq import enqueue[/grey70]")
    console.print("  [grey70]await enqueue('send_welcome_email', user_id=123)[/grey70]")
