# Redis Implementation Plan

## The Challenge

Currently `paxx feature add` handles **domain features** (like products) - they're self-contained in `features/<name>/`. Redis is **infrastructure** - it modifies core files, docker-compose, and dependencies. Keep these separate.

---

## Proposed Architecture

Create a new **infra system** separate from domain features:

```
src/paxx/
├── features/              # Domain features (existing)
│   └── example_products/
├── infra/                 # NEW: Infrastructure components
│   ├── __init__.py
│   └── redis/
│       ├── __init__.py
│       ├── config.py          # InfraConfig
│       ├── templates/
│       │   └── cache.py.jinja # core/cache.py template
│       ├── docker_service.yml # Service definition to merge
│       └── dependencies.txt   # Packages to add
└── cli/
    ├── feature.py         # Existing: paxx feature add/create
    └── infra.py           # NEW: paxx infra add/list
```

---

## Files to Create/Modify

### 1. Infra module

`src/paxx/infra/__init__.py`:

```python
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
        d.name for d in infra_root.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    ]
```

### 2. Redis infra component

`src/paxx/infra/redis/config.py`:

```python
from dataclasses import dataclass, field

@dataclass
class InfraConfig:
    name: str = "redis"
    docker_service: str = "redis"
    core_files: list[str] = field(default_factory=lambda: ["cache.py"])
    dependencies: list[str] = field(default_factory=lambda: ["redis>=5.0"])
    env_vars: dict = field(default_factory=lambda: {
        "REDIS_URL": "redis://localhost:6379/0"
    })
```

`src/paxx/infra/redis/templates/cache.py.jinja`:

```python
"""Redis cache client with async support."""
from redis.asyncio import Redis
from functools import lru_cache
from settings import settings

@lru_cache
def get_redis_client() -> Redis:
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis() -> Redis:
    """Dependency for FastAPI routes."""
    return get_redis_client()

# Common cache operations
async def cache_get(key: str) -> str | None:
    client = get_redis_client()
    return await client.get(key)

async def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    client = get_redis_client()
    await client.set(key, value, ex=ttl)

async def cache_delete(key: str) -> None:
    client = get_redis_client()
    await client.delete(key)
```

`src/paxx/infra/redis/docker_service.yml`:

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5
```

`src/paxx/infra/redis/dependencies.txt`:

```
redis>=5.0
```

### 3. New CLI module

`src/paxx/cli/infra.py`:

```python
import typer
from rich.console import Console
from pathlib import Path

from paxx.infra import get_infra_dir, list_infra

app = typer.Typer(help="Manage infrastructure components")
console = Console()


@app.command()
def add(name: str, force: bool = False):
    """Add an infrastructure component (redis, tasks, storage, etc.)."""
    infra_dir = get_infra_dir(name)
    if not infra_dir:
        available = ", ".join(list_infra())
        console.print(f"[red]Unknown infra: {name}[/red]")
        console.print(f"Available: {available}")
        raise typer.Exit(1)

    # 1. Copy templates to core/
    _copy_templates(infra_dir / "templates", Path("core"))

    # 2. Merge docker service into docker-compose.yml
    _merge_docker_service(infra_dir / "docker_service.yml")

    # 3. Add dependencies to pyproject.toml
    _add_dependencies(infra_dir / "dependencies.txt")

    # 4. Add env vars to settings.py and .env.example
    _add_env_vars(infra_dir)

    console.print(f"[bold green]Added {name} infrastructure[/bold green]")


@app.command("list")
def list_cmd():
    """List available infrastructure components."""
    infra = list_infra()
    console.print("[bold]Available infrastructure:[/bold]")
    for name in infra:
        console.print(f"  - {name}")
```

### 4. Register in main CLI

`src/paxx/cli/main.py` — add infra subcommand:

```python
from paxx.cli import infra

app.add_typer(infra.app, name="infra")
```

### 5. Helper functions

In `src/paxx/cli/infra.py`:

```python
def _copy_templates(templates_dir: Path, dest: Path):
    """Copy and render templates to destination."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(templates_dir))
    dest.mkdir(exist_ok=True)

    for template_file in templates_dir.glob("*.jinja"):
        template = env.get_template(template_file.name)
        output_name = template_file.stem  # Remove .jinja
        output_path = dest / output_name
        output_path.write_text(template.render())
        console.print(f"  [green]Created[/green] {output_path}")


def _merge_docker_service(service_file: Path):
    """Add service definition to docker-compose.yml."""
    import yaml

    compose_path = Path("docker-compose.yml")
    with open(compose_path) as f:
        compose = yaml.safe_load(f)

    with open(service_file) as f:
        new_service = yaml.safe_load(f)

    service_name = list(new_service.keys())[0]
    compose["services"][service_name] = new_service[service_name]

    if "volumes" not in compose:
        compose["volumes"] = {}
    compose["volumes"][f"{service_name}_data"] = None

    with open(compose_path, "w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

    console.print(f"  [green]Updated[/green] docker-compose.yml")


def _add_dependencies(deps_file: Path):
    """Add dependencies to pyproject.toml."""
    import tomllib
    import tomli_w

    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)

    deps = deps_file.read_text().strip().split("\n")
    current = pyproject["project"]["dependencies"]

    for dep in deps:
        if dep not in current:
            current.append(dep)

    with open("pyproject.toml", "wb") as f:
        tomli_w.dump(pyproject, f)

    console.print(f"  [green]Updated[/green] pyproject.toml")


def _add_env_vars(infra_dir: Path):
    """Add environment variables to settings.py and .env.example."""
    # Load config to get env_vars
    # Use AST to find Settings class and add new fields
    # Similar pattern to _register_router_in_main()
    pass
```

---

## User Experience

```bash
# List available infra
paxx infra list
# Available infrastructure:
#   - redis
#   - tasks
#   - storage
#   - email

# Add Redis
paxx infra add redis

# Output:
#   Created core/cache.py
#   Updated docker-compose.yml
#   Updated pyproject.toml
#   Updated settings.py
# Added redis infrastructure
#
# Next steps:
#   1. Run: uv sync
#   2. Start services: docker compose up -d
#   3. Import in your code:
#      from core.cache import cache_get, cache_set, get_redis
```

---

## New Dependencies for Paxx CLI

Add to `src/paxx`'s pyproject.toml:

- `pyyaml` — for docker-compose manipulation
- `tomli-w` — for pyproject.toml writing (tomllib is stdlib for reading)

---

## Summary

| Component | Action |
|-----------|--------|
| `src/paxx/infra/` | New infra module with redis component |
| `src/paxx/cli/infra.py` | New CLI: `paxx infra add/list` |
| `docker-compose.yml` | Auto-merge redis service |
| `pyproject.toml` | Auto-add `redis>=5.0` |
| `settings.py` | Auto-add `REDIS_URL` field |
| `core/cache.py` | Create from template |
