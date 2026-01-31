# Introduction

Do not read files in notes/ dir unless you are asked to read or modify them or add a new file.

# Paxx Architecture

## Overview

Paxx is a FastAPI project scaffolding CLI that generates production-ready code using FastAPI, SQLAlchemy async, Pydantic v2, and Alembic. The core philosophy is **no framework lock-in** — generated projects are standalone Python code with no hidden abstractions. Users can migrate away from the paxx CLI after bootstrapping.

**Version:** 0.1.1
**Python:** >=3.12
**Entry Point:** `src/paxx/cli/main.py` (Typer app)

## Source Structure

```
src/paxx/
├── __init__.py                 # Version and package metadata
├── cli/                        # CLI commands (Typer-based)
│   ├── main.py                 # Entry point, registers all subcommands
│   ├── bootstrap.py            # Project scaffolding (paxx bootstrap)
│   ├── feature.py              # Feature management (paxx feature create/add/list)
│   ├── infra.py                # Infrastructure components (paxx infra add/list)
│   ├── db.py                   # Database migrations (paxx db migrate/upgrade/downgrade)
│   ├── deploy.py               # Deployment configs (paxx deploy add)
│   ├── docker.py               # Docker compose wrappers (paxx docker up/down/logs)
│   ├── start.py                # Dev server (paxx start)
│   └── utils.py                # Shared utilities (validation, Jinja2, project context)
│
└── templates/                  # All Jinja2 templates
    ├── project/                # Project scaffolding (main.py, settings.py, docker, core/)
    ├── features/               # Feature templates
    │   ├── feature_blueprint/  # Blueprint for new features (models, schemas, services, routes)
    │   ├── health/             # Built-in health check feature
    │   └── example_products/   # Complete CRUD example with e2e tests
    ├── infra/                  # Infrastructure components
    │   ├── redis/              # Async Redis caching
    │   ├── arq/                # Background task queue
    │   ├── storage/            # S3/MinIO object storage
    │   ├── websocket/          # WebSocket with rooms
    │   ├── postgis/            # PostGIS geospatial
    │   └── metrics/            # Prometheus + OpenTelemetry
    └── deploys/                # Deployment configurations
        └── linux-server/       # Traefik + systemd + SSL
```

## Generated Project Layout

```
<project>/
├── main.py                     # FastAPI app factory with lifespan
├── settings.py                 # Pydantic Settings (env-aware)
├── alembic.ini                 # Migration config
├── pyproject.toml              # Dependencies
├── docker-compose.yml          # Local dev environment
├── Dockerfile / Dockerfile.dev # Container images
├── .env / .env.example         # Environment variables
│
├── core/                       # Core utilities
│   ├── exceptions.py           # Custom exceptions + handlers
│   ├── middleware.py           # Request/response middleware
│   ├── logging.py              # JSON/console logging config
│   ├── dependencies.py         # FastAPI dependencies (pagination)
│   └── schemas.py              # Shared schemas (ListResponse, PaginationMeta)
│
├── db/                         # Database
│   ├── database.py             # Async SQLAlchemy, Base, get_db, BaseModel
│   └── migrations/             # Alembic migrations
│
├── features/                   # Domain features
│   └── <name>/                 # Each feature has:
│       ├── config.py           # Router prefix, tags
│       ├── models.py           # SQLAlchemy models
│       ├── schemas.py          # Pydantic schemas
│       ├── services.py         # Async business logic
│       └── routes.py           # FastAPI endpoints
│
├── e2e/                        # End-to-end tests
│   ├── conftest.py             # Test fixtures
│   └── test_*.py               # API tests
│
└── deploy/                     # Deployment configs (added by paxx deploy)
```

---

# CLI Command Reference

## `paxx bootstrap <name>`
**File:** `src/paxx/cli/bootstrap.py`

Scaffolds a new project with complete directory structure.

```python
def create_project(
    name: str,
    output_dir: Path = Path("."),
    description: str = "",
    author: str = "Author",
    force: bool = False,
) -> None
```

- `paxx bootstrap myproject` — Creates `./myproject/`
- `paxx bootstrap .` — Bootstraps in current directory
- `--force/-f` — Skip confirmation prompts (CI-friendly)

**Template context:** `project_name`, `project_name_snake`, `project_description`, `author_name`

---

## `paxx start`
**File:** `src/paxx/cli/start.py`

Starts uvicorn dev server.

```python
def start(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
    workers: int = 1,
) -> None
```

Runs: `uv run uvicorn main:app --reload`

---

## `paxx feature <subcommand>`
**File:** `src/paxx/cli/feature.py`

### `paxx feature create <name>`
Creates new feature from blank template.

- Renders: `config.py`, `models.py`, `schemas.py`, `services.py`, `routes.py`
- Output: `features/<name>/`

### `paxx feature add <feature>`
Adds pre-built bundled feature.

- Copies feature from `templates/features/<feature>/`
- **Auto-registers router** in `main.py` using AST parsing
- Copies e2e tests to `e2e/`
- `--force/-f` to overwrite existing

**AST registration flow:**
1. Parses `features/<name>/config.py` to extract `prefix` and `tags`
2. Inserts import: `from features.{name}.routes import router as {name}_router`
3. Inserts: `app.include_router({name}_router, prefix="...", tags=[...])`

### `paxx feature list`
Lists available bundled features.

---

## `paxx infra <subcommand>`
**File:** `src/paxx/cli/infra.py`

### `paxx infra add <component>`
Adds infrastructure component.

**Available:** `redis`, `arq`, `storage`, `websocket`, `postgis`, `metrics`

**Installation process:**
1. Renders templates to `services/` (e.g., `services/cache.py`)
2. Merges Docker service into `docker-compose.yml`
3. Adds dependencies to `pyproject.toml`
4. Adds env vars to `settings.py` and `.env.example`

**Each component has:** `config.py` (InfraConfig dataclass), `docker_service.yml`, `dependencies.txt`, `templates/`

### `paxx infra list`
Shows available components with descriptions.

---

## `paxx db <subcommand>`
**File:** `src/paxx/cli/db.py`

Alembic wrappers.

| Command | Description |
|---------|-------------|
| `paxx db migrate "<msg>"` | Create migration (`--autogenerate` default) |
| `paxx db upgrade [rev]` | Apply migrations (default: `head`) |
| `paxx db downgrade [rev]` | Revert migrations (default: `-1`) |
| `paxx db status` | Show current revision |
| `paxx db history` | Show migration history |
| `paxx db heads` | Show branch heads |

---

## `paxx docker <subcommand>`
**File:** `src/paxx/cli/docker.py`

Docker Compose wrappers.

| Command | Description |
|---------|-------------|
| `up` | Start containers (`-d` detach, `-b` build) |
| `down` | Stop containers (`-v` delete volumes) |
| `build` | Rebuild images (`--no-cache`) |
| `logs` | Show logs (`-f` follow) |
| `ps` | Container status |
| `exec <svc> [cmd]` | Run command (default: bash in app) |

---

## `paxx deploy add <type>`
**File:** `src/paxx/cli/deploy.py`

Adds deployment configuration.

**Available:** `linux-server` (Traefik + systemd + SSL)

Creates:
- `deploy/linux-server/` — Shell scripts, docker-compose, traefik config
- `.github/workflows/build.yml` — GitHub Actions CI/CD

---

# Utilities Reference

**File:** `src/paxx/cli/utils.py`

Before implementing a function, check if it already exists here. Add common utils here for reuse.

### Name Handling
```python
validate_name(name, entity_type="name")  # Validates ^[a-zA-Z][a-zA-Z0-9_-]*$
to_snake_case(name)                       # Converts to snake_case
```

### Templates
```python
get_templates_dir()           # Returns templates/ path
create_jinja_env(dir=None)    # Creates Jinja2 Environment
```

### Project Context
```python
@dataclass
class ProjectContext:
    root: Path
    features_dir: Path
    deploy_dir: Path

check_project_context(require_settings=True)  # Validates project structure
```

### File Operations
```python
check_required_file(filename, error_context)  # Validates file exists
run_command(cmd, check_file=None, capture=False)  # Subprocess runner
```

---

# Key Patterns

## Domain-Driven Features
Each feature is self-contained under `features/<name>/`:
- `models.py` — SQLAlchemy models inheriting `BaseModel`
- `schemas.py` — Pydantic schemas (Create, Update, Public)
- `services.py` — Async business logic functions
- `routes.py` — FastAPI endpoints delegating to services
- `config.py` — Router metadata (prefix, tags)

## App Factory Pattern
```python
# main.py
def create_app() -> FastAPI:
    app = FastAPI(...)
    register_exception_handlers(app)
    register_middleware(app)
    app.include_router(...)
    return app

app = create_app()
```

## Async Throughout
- Database: `AsyncSession` from SQLAlchemy async
- All routes and services are `async def`
- Dependencies use async generators

## Database Inheritance
```python
class BaseModel(TimestampMixin, Base):
    __abstract__ = True
    id: Mapped[UUIDPK]
    # Inherits: created_at, updated_at
```

## Feature Auto-Registration (AST)
When adding bundled features, paxx uses `ast` module to:
1. Parse `config.py` for router metadata
2. Insert import statement in `main.py`
3. Insert `app.include_router()` call

---

# Infrastructure Components

| Component | Templates | Docker Service | Key Env Vars |
|-----------|-----------|----------------|--------------|
| **redis** | `core/cache.py` | Redis 7 Alpine | `REDIS_URL` |
| **arq** | `core/arq.py`, `core/tasks.py` | (uses redis) | `ARQ_REDIS_URL`, `ARQ_MAX_JOBS` |
| **storage** | `core/storage.py` | MinIO | `STORAGE_BACKEND`, `STORAGE_S3_*` |
| **websocket** | `core/ws.py` | (optional redis) | — |
| **postgis** | `core/geo.py` | Upgrades postgres | — |
| **metrics** | `core/metrics.py`, `core/tracing.py` | Jaeger | Jaeger endpoint vars |

---

# Development Guidelines

## Naming Conventions

| Context | Convention | Examples |
|---------|------------|----------|
| Python modules/packages | `snake_case` | `feature_blueprint/`, `example_products/`, `utils.py` |
| Non-Python directories | `kebab-case` | `linux-server/`, `docker-compose.yml` |
| Python files | `snake_case` | `bootstrap.py`, `main.py` |
| Config/infra files | `kebab-case` | `docker-compose.yml`, `.env.example` |

**Rationale:**
- Python requires `snake_case` for importable modules (`from feature_blueprint import ...`)
- DevOps/deployment directories use `kebab-case` (industry standard for non-Python assets)

## CLI Output Styling

**Python CLI code** — use `console.print()` with rich markup:
```python
from rich.console import Console
console = Console()

console.print("[red]Error: Something failed[/red]")
console.print("[bold green]Success![/bold green]")
console.print(f"  [green]Created[/green] {file_path}")
```

**Generated shell scripts** (templates) — use `echo`:
```bash
echo "Deploying application..."
echo "Done!"
```

## Jinja2 Template Context

**Project bootstrap:**
```python
context = {
    "project_name": name,
    "project_name_snake": snake_case_name,
    "project_description": description,
    "author_name": author,
}
```

**Feature creation:**
```python
context = {
    "feature_name": feature_name,
    "feature_description": description,
}
```

**Common filters:** `capitalize`, `replace`, `default`

## Adding New CLI Commands

1. Create new file in `src/paxx/cli/` (e.g., `mycommand.py`)
2. Create Typer app: `app = typer.Typer()`
3. Register in `main.py`: `app.add_typer(mycommand_app, name="mycommand")`

## Adding New Infrastructure Component

1. Create `src/paxx/templates/infra/<name>/`
2. Add `config.py` with `InfraConfig` dataclass
3. Add `docker_service.yml`, `dependencies.txt`
4. Add templates in `templates/` subdirectory
5. Component auto-discovered by `paxx infra add`

## Adding New Bundled Feature

1. Create `src/paxx/templates/features/<name>/`
2. Include: `config.py`, `models.py`, `schemas.py`, `services.py`, `routes.py`
3. Optionally add `e2e/` with tests
4. Feature auto-discovered by `paxx feature add`

---

# File Modification Patterns

## Modifying docker-compose.yml
Use PyYAML to load, modify, and dump:
```python
import yaml
with open("docker-compose.yml") as f:
    compose = yaml.safe_load(f)
compose["services"]["new_service"] = {...}
with open("docker-compose.yml", "w") as f:
    yaml.dump(compose, f, default_flow_style=False)
```

## Modifying pyproject.toml
Use tomli (read) + tomli_w (write):
```python
import tomli, tomli_w
with open("pyproject.toml", "rb") as f:
    config = tomli.load(f)
config["project"]["dependencies"].append("new-package>=1.0")
with open("pyproject.toml", "wb") as f:
    tomli_w.dump(config, f)
```

## Modifying main.py (AST)
Use `ast` module to parse and find insertion points:
```python
import ast
with open("main.py") as f:
    tree = ast.parse(f.read())
# Walk tree to find FunctionDef for create_app, etc.
```

---

# Testing

**Location:** `tests/`
- `tests/unit/` — Template rendering, utilities
- `tests/integration/` — CLI commands, full flows

**Run:** `uv run pytest`

**Generated project tests:** `e2e/` directory with `pytest-asyncio`
