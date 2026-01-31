"""Installation script for metrics infrastructure component."""

from pathlib import Path

from rich.console import Console

from paxx.templates.installer import TemplateInstaller

console = Console()


def install(project_path: Path, force: bool = False) -> None:
    """Install metrics infrastructure component.

    Args:
        project_path: Path to the project root.
        force: Whether to overwrite existing files.
    """
    installer = TemplateInstaller(project_path)
    component_dir = Path(__file__).parent

    # Copy templates to services/
    installer.copy_templates(component_dir / "templates", project_path / "services")

    # Merge docker service (Jaeger)
    installer.merge_docker_service(component_dir / "docker_service.yml")

    # Add dependencies
    installer.add_dependencies(component_dir / "dependencies.txt")

    # Add env vars
    installer.add_env_vars_from_file(component_dir / "env.json")

    # Print success and next steps
    installer.print_success("metrics")
    installer.print_next_steps()
