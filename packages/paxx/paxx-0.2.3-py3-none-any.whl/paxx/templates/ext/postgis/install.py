"""Installation script for PostGIS extension."""

from pathlib import Path

from rich.console import Console
from ruamel.yaml import YAML

from paxx.templates.installer import TemplateInstaller

console = Console()


def _upgrade_postgres_to_postgis(project_path: Path) -> None:
    """Upgrade postgres service in docker-compose.yml to use PostGIS image.

    Finds the postgres service (named db, postgres, or database) and updates
    its image from postgres:X to postgis/postgis:X-3.4.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)

    compose_path = project_path / "docker-compose.yml"
    if not compose_path.exists():
        console.print("  [yellow]Warning:[/yellow] docker-compose.yml not found")
        return

    with open(compose_path) as f:
        compose = yaml.load(f)

    services = compose.get("services", {})

    # Find postgres service (might be named db, postgres, database)
    pg_service = None
    pg_name = None
    for name in ["db", "postgres", "database"]:
        if name in services:
            pg_service = services[name]
            pg_name = name
            break

    if not pg_service:
        console.print(
            "  [yellow]Warning:[/yellow] "
            "No postgres service found in docker-compose.yml"
        )
        console.print(
            "  [grey70]Expected service named: db, postgres, or database[/grey70]"
        )
        return

    # Check if already using postgis
    current_image = pg_service.get("image", "")
    if "postgis" in current_image:
        console.print("  [yellow]Already using PostGIS image[/yellow]")
        return

    # Extract version from current image (e.g., postgres:16 -> 16)
    version = "16"
    if ":" in current_image:
        version = current_image.split(":")[1].split("-")[0]

    # Update to PostGIS image
    pg_service["image"] = f"postgis/postgis:{version}-3.4"

    with open(compose_path, "w") as f:
        yaml.dump(compose, f)

    console.print(
        f"  [green]Updated[/green] {pg_name} service to postgis/postgis:{version}-3.4"
    )


def _add_geoalchemy2_import_to_mako(project_path: Path) -> None:
    """Add geoalchemy2 import to Alembic migration template."""
    mako_path = project_path / "db/migrations/script.py.mako"
    if not mako_path.exists():
        console.print("  [yellow]Warning:[/yellow] script.py.mako not found")
        return

    content = mako_path.read_text()

    # Check if already added
    if "import geoalchemy2" in content:
        console.print("  [yellow]geoalchemy2 import already in script.py.mako[/yellow]")
        return

    # Insert after "import sqlalchemy as sa"
    content = content.replace(
        "import sqlalchemy as sa",
        "import geoalchemy2\nimport sqlalchemy as sa",
    )

    mako_path.write_text(content)
    console.print("  [green]Updated[/green] db/migrations/script.py.mako")


def install(project_path: Path, force: bool = False) -> None:
    """Install PostGIS extension.

    Args:
        project_path: Path to the project root.
        force: Whether to overwrite existing files.
    """
    installer = TemplateInstaller(project_path)
    component_dir = Path(__file__).parent

    # PostGIS-specific: upgrade postgres to postgis image
    _upgrade_postgres_to_postgis(project_path)

    # PostGIS-specific: add geoalchemy2 import to mako template
    _add_geoalchemy2_import_to_mako(project_path)

    # Copy templates to services/
    installer.copy_templates(component_dir / "templates", project_path / "services")

    # Add dependencies
    installer.add_dependencies(component_dir / "dependencies.txt")

    # Print success and next steps
    installer.print_success("postgis")
    installer.print_next_steps()

    # PostGIS-specific usage instructions
    console.print()
    console.print(
        "[bold]Important:[/bold] Restart your database "
        "to use the new PostGIS image:"
    )
    console.print("  [grey70]docker compose down && docker compose up -d[/grey70]")
    console.print()
    console.print("[bold]Usage in models:[/bold]")
    console.print("  [grey70]from services.geo import Geography[/grey70]")
    console.print("  [grey70]from sqlalchemy.orm import mapped_column[/grey70]")
    console.print()
    console.print("  [grey70]class Location(Base):[/grey70]")
    console.print("  [grey70]    __tablename__ = 'locations'[/grey70]")
    console.print("  [grey70]    location = mapped_column([/grey70]")
    console.print("  [grey70]        Geography(geometry_type='POINT', srid=4326),[/grey70]")  # noqa: E501
    console.print("  [grey70]        index=True,  # Creates GIST index[/grey70]")
    console.print("  [grey70]    )[/grey70]")
    console.print()
    console.print("[bold]Query helpers:[/bold]")
    console.print(
        "  [grey70]from services.geo import "
        "distance_within, bbox_filter, distance_meters[/grey70]"
    )
    console.print()
    console.print("  [grey70]# Filter by radius (100m)[/grey70]")
    console.print("  [grey70]stmt = select(Location).where([/grey70]")
    console.print(
        "  [grey70]    distance_within("
        "Location.location, lat=52.52, lng=13.4, radius_meters=100)[/grey70]"
    )
    console.print("  [grey70])[/grey70]")
    console.print()
    console.print("  [grey70]# Viewport/bounding box query[/grey70]")
    console.print("  [grey70]stmt = select(Location).where([/grey70]")
    console.print(
        "  [grey70]    bbox_filter("
        "Location.location, west=13.0, south=52.0, east=14.0, north=53.0)[/grey70]"
    )
    console.print("  [grey70])[/grey70]")
