# Implementation Notes

## Progress Checklist

### Phase 1: Foundation
- [x] **1.1 Project Setup**
  - [x] Initialize Python package structure with `pyproject.toml` (uv-compatible)
  - [x] Use uv for package management
  - [x] Set up development tools (ruff, mypy, pre-commit)
  - [x] Configure pytest with async support
  - [x] Create basic CI/CD pipeline (GitHub Actions)
- [x] **1.2 Configuration System**
  - [x] Implement `Settings` class using Pydantic Settings
  - [x] Support for `.env` files and environment variables
  - [x] Settings validation at startup
  - [x] Typed access to configuration values
- [x] **1.3 Database Core**
  - [x] Async SQLAlchemy engine and session factory
  - [x] `BaseModel` with `id`, `created_at`, `updated_at`
  - [x] Database dependency for FastAPI (`get_db`)
  - [x] Alembic setup with async support
  - [x] CLI commands: `db migrate`, `db upgrade`, `db downgrade`
- [x] **1.4 Featurelication Factory**
  - [x] `create_feature()` function for FastAPI instance creation
  - [x] Lifespan management (startup/shutdown)
  - [x] Exception handlers registration
  - [x] Middleware registration

### Phase 2: Core Features
- [ ] **2.1 Logging & Observability** *(skipped for now)*
  - [ ] structlog configuration
  - [ ] Request ID middleware
  - [ ] Request/response logging middleware
  - [ ] Correlation ID propagation
- [ ] **2.2 Authentication** *(skipped for now)*
  - [ ] JWT token utilities (create, verify, refresh)
  - [ ] Password hashing utilities
  - [ ] `get_current_user` dependency
  - [ ] OAuth2 password flow implementation
- [ ] **2.3 Authorization** *(skipped for now)*
  - [ ] Permission checker dependency
  - [ ] Role-based access control
  - [ ] Decorator for route protection
- [x] **2.4 Shared Utilities**
  - [x] Pagination dependency and schemas
  - [x] Standard response schemas (success, error, list)
  - [x] Common exceptions (NotFound, Forbidden, etc.) *(already in core/exceptions.py)*

### Phase 3: Feature System
- [x] **3.1 Feature Structure**
  - [x] Define feature conventions and file structure
  - [x] Create feature template/scaffold
  - [x] Feature configuration class
- [x] **3.2 Feature Registration**
  - [x] Router auto-discovery (optional)
  - [x] Feature initialization hooks
  - [x] Model discovery for Alembic *(already done in 1.3)*
- [ ] **3.3 Example Feature: Users**
  - [ ] Complete implementation as reference
  - [ ] User model, schemas, routes, services
  - [ ] Registration, login, profile endpoints
  - [ ] Full test coverage

### Phase 4: Developer Experience
- [x] **4.1 CLI Tooling**
  - [x] `paxx bootstrap <project>` - Create new project
  - [x] `paxx feature create <name>` - Generate new domain feature
  - [x] `paxx start` - Development server
  - [x] `paxx db` - Database commands
  - [x] `paxx shell` - Interactive shell
- [ ] **4.2 Testing Utilities**
  - [ ] Test client factory
  - [ ] Database fixtures (test DB, transactions)
  - [ ] Authentication helpers for tests
  - [ ] Factory classes for models
- [ ] **4.3 Documentation**
  - [ ] Getting started guide
  - [ ] Feature structure conventions
  - [ ] API reference
  - [ ] Example project

### Phase 5: Advanced Features (Future)
- [ ] **5.1 Caching**
  - [ ] Redis integration
  - [ ] Cache decorator
  - [ ] Cache invalidation patterns
- [ ] **5.2 Background Tasks**
  - [ ] Task queue integration (ARQ/Celery)
  - [ ] Task decorator
  - [ ] Scheduled tasks
- [ ] **5.3 Events**
  - [ ] In-process event bus
  - [ ] Cross-feature communication
  - [ ] Event handlers in features
- [ ] **5.4 WebSockets**
  - [ ] WebSocket manager
  - [ ] Room/channel patterns
  - [ ] Authentication for WebSockets

---

## 1.1 Project Setup - Completed

Implemented the foundation for the paxx CLI tool with uv-compatible package structure.

### What was created:

**Package structure (src layout):**
- `src/paxx/__init__.py` - Package root with version
- `src/paxx/cli/main.py` - Typer CLI entry point with `version` command
- `src/paxx/templates/` - For future Jinja2 templates
- `src/paxx/utils/` - For utility functions

**Configuration files:**
- `pyproject.toml` - uv-compatible with hatchling build backend
  - Runtime deps: typer, jinja2, rich
  - Dev deps: pytest, pytest-asyncio, ruff, mypy, pre-commit
  - Ruff configured for linting and formatting
  - mypy configured in strict mode
  - pytest configured with async support
- `.pre-commit-config.yaml` - ruff and mypy hooks
- `.gitignore` - Python/uv/IDE ignores

**Testing:**
- `tests/conftest.py` - Shared fixtures
- `tests/test_cli.py` - Basic CLI test

**CI/CD:**
- `.github/workflows/ci.yml` - GitHub Actions pipeline
  - Lint job (ruff check + format)
  - Typecheck job (mypy)
  - Test job (pytest on Python 3.12 and 3.13)

### To verify setup works:

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest -v

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy src/paxx

# Try the CLI
uv run paxx --version
```

## 1.2 Configuration System - Completed

Implemented templates for the configuration system that generated projects will use.

### What was created:

**Project templates (`src/paxx/templates/project/`):**
- `settings.py.jinja` - Pydantic Settings class template
- `.env.example.jinja` - Example environment file template
- `pyproject.toml.jinja` - Project configuration template with all required dependencies

### Settings Template Features:

The `settings.py.jinja` template generates a fully-featured configuration module:

- **Pydantic Settings integration** - Uses `pydantic-settings` for typed configuration
- **Environment variable support** - All settings can be overridden via environment variables
- **.env file support** - Automatic loading from `.env` file in project root
- **Validation at startup** - Settings are validated when the featurelication starts
- **Typed access** - Full type hints for IDE autocomplete and type checking

### Available settings in generated projects:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `feature_name` | str | Project name | Featurelication name |
| `debug` | bool | False | Debug mode flag |
| `environment` | Literal | "development" | Environment (development/staging/production) |
| `host` | str | "127.0.0.1" | Server host |
| `port` | int | 8000 | Server port |
| `database_url` | str | sqlite+aiosqlite:///./{project}.db | Async database URL |
| `secret_key` | str | (placeholder) | JWT secret key (min 32 chars) |
| `access_token_expire_minutes` | int | 30 | Token expiration time |
| `cors_origins` | list[str] | ["http://localhost:3000"] | Allowed CORS origins |

### Helper properties:

- `settings.is_development` - Check if running in development
- `settings.is_production` - Check if running in production

### Usage in generated projects:

```python
from settings import settings

# Access configuration
print(settings.feature_name)
print(settings.database_url)

# Check environment
if settings.is_development:
    print("Running in development mode")
```

### Testing:

Added comprehensive tests in `tests/test_settings_template.py`:
- Template rendering tests
- Python syntax validation
- Module import tests
- Settings instantiation tests
- Environment variable override tests
- .env file loading tests
- Property tests (is_development, is_production)

## 1.3 Database Core - Completed

Implemented templates for the database layer that generated projects will use.

### What was created:

**Database templates (`src/paxx/templates/project/core/`):**
- `__init__.py.jinja` - Core package initializer
- `database.py.jinja` - SQLAlchemy async engine, session, and BaseModel

**Alembic templates (`src/paxx/templates/project/migrations/`):**
- `env.py.jinja` - Async-compatible Alembic environment with model auto-discovery
- `script.py.mako.jinja` - Migration script template
- `versions/.gitkeep` - Placeholder for migration versions

**Configuration:**
- `alembic.ini.jinja` - Alembic configuration with ruff post-write hook

**CLI commands (`src/paxx/cli/db.py`):**
- `paxx db migrate "<message>"` - Create a new migration (wraps `alembic revision`)
- `paxx db upgrade [revision]` - Featurely migrations (wraps `alembic upgrade`)
- `paxx db downgrade [revision]` - Revert migrations (wraps `alembic downgrade`)
- `paxx db status` - Show current migration status
- `paxx db history` - Show migration history
- `paxx db heads` - Show current heads

### Database Template Features:

The `database.py.jinja` template generates:

- **Async SQLAlchemy engine** - Configured with connection pooling and debug echo
- **Async session factory** - For dependency injection in FastAPI
- **Base class** - With naming conventions for database constraints
- **TimestampMixin** - Reusable mixin for created_at/updated_at
- **BaseModel** - Abstract base with id (UUIDPK) and timestamps
- **get_db dependency** - FastAPI dependency for database sessions with auto-commit/rollback
- **init_db/close_db** - Lifecycle functions for startup/shutdown

### BaseModel fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int (primary key) | Auto-incrementing integer primary key |
| `created_at` | datetime | Set automatically on insert |
| `updated_at` | datetime | Set automatically on insert and update |

### Naming conventions for constraints:

| Constraint | Pattern |
|------------|---------|
| Index | `ix_<column>` |
| Unique | `uq_<table>_<column>` |
| Check | `ck_<table>_<constraint>` |
| Foreign Key | `fk_<table>_<column>_<referred_table>` |
| Primary Key | `pk_<table>` |

### Alembic Features:

- **Async support** - Uses `async_engine_from_config` for async migrations
- **Model auto-discovery** - Automatically imports models from all features in `features/` directory
- **Ruff formatting** - Post-write hook formats generated migration files
- **Configurable** - Settings override from `settings.py`

### Usage in generated projects:

```python
# In your models (features/users/models.py)
from core.database import BaseModel
from sqlalchemy.orm import Mfeatureed, mfeatureed_column

class User(BaseModel):
    __tablename__ = "users"

    email: Mfeatureed[str] = mfeatureed_column(unique=True)
    name: Mfeatureed[str]

# In your routes (features/users/routes.py)
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db

@router.get("/users")
async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### CLI Usage:

```bash
# Create a new migration
paxx db migrate "add users table"

# Featurely all pending migrations
paxx db upgrade

# Revert last migration
paxx db downgrade

# Check migration status
paxx db status
```

### Testing:

Added comprehensive tests in `tests/test_database_template.py`:
- Template rendering tests for database.py
- Template rendering tests for alembic env.py
- Template rendering tests for alembic.ini
- Python syntax validation
- AST structure validation
- Module import and structure tests

## 1.4 Featurelication Factory - Completed

Implemented templates for the featurelication factory that generated projects will use.

### What was created:

**Featurelication templates (`src/paxx/templates/project/`):**
- `main.py.jinja` - Featurelication entry point with create_feature() factory

**Core module templates (`src/paxx/templates/project/core/`):**
- `exceptions.py.jinja` - Custom exceptions and exception handlers
- `middleware.py.jinja` - Custom middleware (request ID, timing)

### Featurelication Factory Features:

The `main.py.jinja` template generates:

- **create_feature() function** - Factory function that creates and configures FastAPI instance
- **Lifespan management** - Async context manager for startup/shutdown events
- **Exception handlers registration** - Integrates with core/exceptions.py
- **Middleware registration** - Integrates with core/middleware.py
- **CORS configuration** - Using settings.cors_origins
- **Health check endpoint** - GET /health for monitoring

### Exception Handlers:

The `exceptions.py.jinja` template provides:

| Exception | HTTP Status | Use Case |
|-----------|-------------|----------|
| `FeatureException` | 500 | Base exception class |
| `NotFoundError` | 404 | Resource not found |
| `BadRequestError` | 400 | Invalid input |
| `UnauthorizedError` | 401 | Authentication required |
| `ForbiddenError` | 403 | Insufficient permissions |
| `ConflictError` | 409 | Duplicate resource |

All exceptions return consistent JSON responses:
```json
{
  "message": "Error message",
  "detail": "Optional details"
}
```

### Middleware:

The `middleware.py.jinja` template provides:

| Middleware | Header | Description |
|------------|--------|-------------|
| `request_id_middleware` | X-Request-ID | Generates/propagates unique request ID |
| `timing_middleware` | X-Process-Time | Measures request processing time |

### Usage in generated projects:

```python
# main.py is ready to use
from main import feature

# Register your feature routers
from features.users.routes import router as users_router
feature.include_router(users_router, prefix="/users", tags=["users"])

# Using exceptions in services
from core.exceptions import NotFoundError, BadRequestError

async def get_user(user_id: int):
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found", detail=f"User {user_id} does not exist")
    return user

# Accessing request ID in routes
from fastapi import Request

@router.get("/example")
async def example(request: Request):
    request_id = request.state.request_id
    return {"request_id": request_id}
```

### Testing:

Added comprehensive tests in `tests/test_feature_factory_template.py`:
- main.py template rendering and validity tests
- exceptions.py template rendering and structure tests
- middleware.py template rendering and structure tests
- Module importability tests
- Exception class hierarchy tests

---

## Phase 1 Complete

All Phase 1 (Foundation) components are now implemented:

| Component | Status | Description |
|-----------|--------|-------------|
| 1.1 Project Setup | ✅ Complete | Package structure, tooling, CI/CD |
| 1.2 Configuration System | ✅ Complete | Pydantic Settings templates |
| 1.3 Database Core | ✅ Complete | SQLAlchemy async, Alembic, CLI commands |
| 1.4 Featurelication Factory | ✅ Complete | create_feature(), lifespan, exceptions, middleware |

The framework can now generate a bootable FastAPI featurelication with:
- Configured settings from environment/.env
- Async database with migrations
- Featurelication factory with proper lifecycle management
- Custom exception handling
- Request ID and timing middleware
- Health check endpoint

---

## Phase 2: Core Features

### 2.1 Logging & Observability - Skipped (Placeholder)

*To be implemented later.*

Tasks:
- [ ] structlog configuration
- [ ] Request ID middleware
- [ ] Request/response logging middleware
- [ ] Correlation ID propagation

---

### 2.2 Authentication - Skipped (Placeholder)

*To be implemented later.*

Tasks:
- [ ] JWT token utilities (create, verify, refresh)
- [ ] Password hashing utilities
- [ ] `get_current_user` dependency
- [ ] OAuth2 password flow implementation

---

### 2.3 Authorization - Skipped (Placeholder)

*To be implemented later.*

Tasks:
- [ ] Permission checker dependency
- [ ] Role-based access control
- [ ] Decorator for route protection

---

## 2.4 Core Utilities - Completed

Implemented templates for core utilities that generated projects will use.

### What was created:

**Core templates (`src/paxx/templates/project/core/`):**
- `__init__.py.jinja` - Package initializer with exports
- `dependencies.py.jinja` - FastAPI dependencies (pagination)
- `schemas.py.jinja` - Standard response schemas

### Pagination Support:

The `dependencies.py.jinja` template provides:

| Component | Description |
|-----------|-------------|
| `PaginationParams` | Pydantic model with page and page_size |
| `get_pagination` | FastAPI dependency for query parameter extraction |
| `offset` property | Calculated offset for database queries |
| `limit` property | Alias for page_size |

Query parameters:
- `page`: Page number (1-indexed, default: 1, min: 1)
- `page_size`: Items per page (default: 20, min: 1, max: 100)

### Standard Response Schemas:

The `schemas.py.jinja` template provides:

| Schema | Fields | Use Case |
|--------|--------|----------|
| `SuccessResponse` | message | Simple success messages |
| `ErrorResponse` | message, detail | Error responses (matches exception format) |
| `PaginationMeta` | page, page_size, total_items, total_pages | Pagination metadata |
| `ListResponse[T]` | items, meta | Generic paginated list responses |

### Usage in generated projects:

```python
# Using pagination in routes
from typing import Annotated
from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import PaginationParams, get_pagination
from core.schemas import ListResponse, PaginationMeta

@router.get("/items", response_model=ListResponse[ItemPublic])
async def list_items(
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Get total count
    total = await db.scalar(select(func.count(Item.id)))

    # Get paginated items
    result = await db.execute(
        select(Item)
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    items = result.scalars().all()

    return ListResponse(
        items=items,
        meta=PaginationMeta(
            page=pagination.page,
            page_size=pagination.page_size,
            total_items=total,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size,
        )
    )

# Using standard responses
from core.schemas import SuccessResponse, ErrorResponse

@router.delete("/items/{item_id}")
async def delete_item(item_id: int) -> SuccessResponse:
    # ... delete logic ...
    return SuccessResponse(message="Item deleted successfully")
```

### Note on Common Exceptions:

Common exceptions (`NotFoundError`, `BadRequestError`, `UnauthorizedError`, `ForbiddenError`, `ConflictError`) are already implemented in `core/exceptions.py.jinja` as part of Phase 1.4 (Featurelication Factory). The `ErrorResponse` schema in core/schemas.py matches the format used by exception handlers.

### Testing:

Added comprehensive tests in `tests/test_core_utilities_template.py`:
- dependencies.py template rendering tests
- schemas.py template rendering tests
- __init__.py template rendering tests
- Python syntax validation
- AST structure validation
- Module importability tests
- PaginationParams calculation tests
- Schema instantiation tests

---

## Phase 3: Feature System

## 3.1 Feature Structure - Completed

Implemented templates for the feature structure that defines how domain-specific features are organized in generated projects.

### What was created:

**Feature templates (`src/paxx/templates/features/feature_blueprint/`):**
- `__init__.py.jinja` - Package initializer with feature config import
- `config.py.jinja` - Feature configuration dataclass
- `models.py.jinja` - SQLAlchemy models template with examples
- `schemas.py.jinja` - Pydantic schemas template (Base, Create, Update, Public)
- `services.py.jinja` - Business logic template with example service functions
- `routes.py.jinja` - FastAPI router template with CRUD examples

### Feature Convention (File Structure):

Generated features follow a consistent structure in `features/<feature_name>/`:

```
features/
└── users/                    # Example feature
    ├── __init__.py          # Feature module with config export
    ├── config.py            # Feature configuration (name, prefix, tags)
    ├── models.py            # SQLAlchemy models
    ├── schemas.py           # Pydantic request/response schemas
    ├── services.py          # Business logic layer
    └── routes.py            # FastAPI router endpoints
```

### Feature Configuration Class:

The `config.py.jinja` template generates a dataclass-based configuration:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Feature name (used for internal reference) |
| `verbose_name` | str | Human-readable name |
| `description` | str | Description of feature functionality |
| `prefix` | str | URL prefix for routes (e.g., "/users") |
| `tags` | list[str] | OpenAPI tags for documentation |

### Schema Conventions:

The `schemas.py.jinja` template defines four schema patterns:

| Schema | Purpose |
|--------|---------|
| `*Base` | Common fields shared across schemas |
| `*Create` | Request body for creating resources (POST) |
| `*Update` | Request body for updating resources (PUT/PATCH) |
| `*Public` | Response schema with `from_attributes=True` for ORM |

### Service Layer Pattern:

The `services.py.jinja` template encourages:
- All business logic in services (not routes)
- Database session passed as parameter
- Use of exceptions from `core.exceptions`
- Return domain objects or None

### Route Conventions:

The `routes.py.jinja` template provides examples for:
- `GET /` - List with pagination
- `GET /{id}` - Get single resource
- `POST /` - Create resource (201 status)
- `PUT /{id}` - Update resource
- `DELETE /{id}` - Delete resource

### Usage in generated projects:

```python
# Register an feature's routes in main.py
from features.users.routes import router as users_router
from features.users.config import feature_config as users_config

feature.include_router(
    users_router,
    prefix=users_config.prefix,
    tags=users_config.tags,
)
```

### Testing:

Added comprehensive tests in `tests/test_feature_structure_template.py`:
- config.py template rendering and validity tests
- models.py template rendering and validity tests
- schemas.py template rendering and structure tests
- services.py template rendering and validity tests
- routes.py template rendering and validity tests
- __init__.py template rendering and validity tests
- Module importability tests
- Different feature name handling tests (snake_case, single word)

---

## Phase 4: Developer Experience

## 4.1 CLI Tooling - Completed

Implemented the main CLI commands for project scaffolding and development workflow.

### What was created:

**CLI Commands (`src/paxx/cli/`):**
- `bootstrap.py` - `paxx bootstrap <project>` command for creating new projects
- `feature.py` - `paxx feature` subcommands for managing features
- `start.py` - `paxx start` command for starting the development server
- `shell.py` - `paxx shell` command for interactive Python shell

### Command: `paxx bootstrap <project>`

Creates a new paxx project with the complete project structure.

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output-dir` | `-o` | `.` | Directory to create project in |
| `--description` | `-d` | "" | Project description |
| `--author` | `-a` | "Author" | Author name |

**Generated Structure:**
```
<project>/
├── main.py              # Featurelication entry point
├── settings.py          # Pydantic Settings configuration
├── pyproject.toml       # Project configuration
├── alembic.ini          # Alembic configuration
├── .env                 # Environment variables (from template)
├── .env.example         # Example environment file
├── README.md            # Project readme
├── .gitignore           # Git ignore patterns
├── core/                # Core utilities
│   ├── __init__.py
│   ├── database.py      # SQLAlchemy async setup
│   ├── exceptions.py    # Custom exceptions
│   ├── middleware.py    # Custom middleware
│   ├── features.py          # Feature discovery utilities
│   ├── dependencies.py  # FastAPI dependencies
│   └── schemas.py       # Standard response schemas
├── migrations/          # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── features/                # Domain features directory
└── tests/               # Test directory
    ├── __init__.py
    └── conftest.py
```

**Example usage:**
```bash
paxx bootstrap myproject
paxx bootstrap my-api --description "My REST API" --author "John Doe"
paxx bootstrap myproject -o /path/to/projects
```

### Command: `paxx feature create <name>`

Creates a new domain feature within an existing paxx project.

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--description` | `-d` | "" | Feature description |

**Generated Structure:**
```
features/<feature_name>/
├── __init__.py          # Feature module
├── config.py            # Feature configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── services.py          # Business logic
└── routes.py            # API routes
```

**Example usage:**
```bash
paxx feature create users
paxx feature create blog_posts --description "Blog post management"
paxx feature create user-profiles  # Converted to user_profiles
```

### Command: `paxx feature add <name>`

Adds a bundled feature template to your project.

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--list` | `-l` | false | List available features |
| `--force` | `-f` | false | Overwrite existing feature |

**Example usage:**
```bash
paxx feature add auth          # Add authentication system
paxx feature list      # List available features
paxx feature add auth --force  # Overwrite existing auth feature
```

### Command: `paxx start`

Starts the development server using uvicorn.

**Options:**
| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--host` | `-h` | `127.0.0.1` | Host to bind to |
| `--port` | `-p` | `8000` | Port to bind to |
| `--reload/--no-reload` | `-r/-R` | `--reload` | Enable auto-reload |
| `--workers` | `-w` | `1` | Number of workers (without reload) |

**Example usage:**
```bash
paxx start                         # localhost:8000 with auto-reload
paxx start --port 3000             # Custom port
paxx start --host 0.0.0.0          # Bind to all interfaces
paxx start --no-reload --workers 4 # Production-like mode
```

### Command: `paxx shell`

Launches an interactive Python shell with featurelication context pre-loaded.

**Pre-loaded objects:**
| Object | Description |
|--------|-------------|
| `feature` | FastAPI featurelication instance |
| `settings` | Featurelication settings |
| `async_session_factory` | Database session factory |
| `AsyncSession` | SQLAlchemy async session class |
| `Base` | SQLAlchemy declarative base |
| `<Model>` | All models from features (auto-discovered) |

Uses IPython if available, otherwise falls back to the standard Python REPL.

**Example usage:**
```bash
paxx shell
```

### Testing:

Added comprehensive tests in `tests/test_cli_commands.py`:
- `paxx bootstrap` command tests (7 tests)
  - Help text verification
  - Project creation with correct structure
  - Custom options (description, author)
  - Error handling (existing directory)
  - Name validation and normalization
  - Output directory option
- `paxx feature create` command tests (6 tests)
  - Help text verification
  - Feature creation with correct structure
  - Description option
  - Error handling (existing feature, outside project)
  - Name normalization (hyphen to snake_case)
- `paxx start` command tests (2 tests)
  - Help text verification
  - Project context validation
- `paxx shell` command tests (2 tests)
  - Help text verification
  - Project context validation