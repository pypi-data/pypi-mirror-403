"""Installation script for storage infrastructure component."""

from pathlib import Path

from rich.console import Console

from paxx.templates.installer import TemplateInstaller

console = Console()


def install(project_path: Path, force: bool = False) -> None:
    """Install storage infrastructure component.

    Args:
        project_path: Path to the project root.
        force: Whether to overwrite existing files.
    """
    installer = TemplateInstaller(project_path)
    component_dir = Path(__file__).parent

    # Copy templates to services/
    installer.copy_templates(component_dir / "templates", project_path / "services")

    # Merge docker service (MinIO)
    installer.merge_docker_service(component_dir / "docker_service.yml")

    # Add dependencies
    installer.add_dependencies(component_dir / "dependencies.txt")

    # Add env vars
    installer.add_env_vars_from_file(component_dir / "env.json")

    # Print success and next steps
    installer.print_success("storage")
    installer.print_next_steps()

    # Storage-specific usage instructions
    console.print()
    console.print("[bold]Local development:[/bold]")
    console.print("  Files are stored in ./uploads by default")
    console.print()
    console.print("[bold]MinIO testing (S3-compatible):[/bold]")
    console.print("  1. Start MinIO: [grey70]docker compose up -d minio[/grey70]")
    console.print("  2. Open console: [grey70]http://localhost:9001[/grey70]")
    console.print("  3. Create a bucket in the console")
    console.print("  4. Set env vars:")
    console.print("     [grey70]STORAGE_BACKEND=s3[/grey70]")
    console.print("     [grey70]STORAGE_S3_BUCKET=my-bucket[/grey70]")
    console.print("     [grey70]STORAGE_S3_ENDPOINT_URL=http://minio:9000[/grey70]")
    console.print("     [grey70]STORAGE_S3_ACCESS_KEY=minioadmin[/grey70]")
    console.print("     [grey70]STORAGE_S3_SECRET_KEY=minioadmin[/grey70]")
    console.print()
    console.print("[bold]Usage in code:[/bold]")
    console.print("  [grey70]from services.storage import get_storage[/grey70]")
    console.print("  [grey70]storage = get_storage()[/grey70]")
    console.print(
        "  [grey70]url = await storage.upload('path/file.jpg', data)[/grey70]"
    )
