# paxx Framework - Initial Idea

A domain-oriented Python web framework built on top of FastAPI.

## Philosophy

- **Don't reinvent the wheel** - Use FastAPI's features directly
- **Domain-driven structure** - Organize code by business domains (like Django features)
- **Minimal magic** - Explicit over implicit, easy to understand
- **Async-first** - Full async support throughout

## Project Structure

```
my_project/
├── main.py                     # Featurelication entry point
├── settings.py                 # Global settings (Pydantic Settings)
├── features/
│   ├── users/
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI router
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── services.py         # Business logic
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_routes.py
│   │       └── test_services.py
│   ├── products/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── dependencies.py
│   │   └── tests/
│   └── orders/
│       └── ...
├── core/
│   ├── __init__.py
│   ├── database.py             # DB engine, session, base model
│   ├── security.py             # Auth utilities
│   ├── exceptions.py           # Global exception handlers
│   ├── middleware.py           # Custom middleware
│   ├── dependencies.py         # Common dependencies (pagination, etc.)
│   ├── schemas.py              # Common schemas (responses, errors)
│   └── utils.py                # Helper functions
├── cli/
│   ├── __init__.py
│   └── commands.py             # Typer CLI commands
├── migrations/                 # Alembic migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py             # Shared fixtures
│   └── test_integration.py
└── pyproject.toml
```

## Core Components

### 1. Database (SQLAlchemy 2.0 + Alembic)
- Async session management
- Base model with common fields (id, created_at, updated_at)
- Alembic for migrations

### 2. Configuration (Pydantic Settings)
- Environment-based configuration
- Validation of settings at startup
- Support for .env files

### 3. Authentication & Authorization
- Built on FastAPI's security utilities
- JWT-based authentication
- Permission/role system

### 4. Logging (structlog)
- Structured JSON logging
- Request ID propagation
- Correlation across services

### 5. CLI (Typer)
- Database migrations
- User management
- Custom commands per feature

## Feature Structure Convention

Each feature (domain) follows a consistent structure:

| File | Purpose |
|------|---------|
| `routes.py` | FastAPI router with endpoints |
| `models.py` | SQLAlchemy ORM models |
| `schemas.py` | Pydantic request/response schemas |
| `services.py` | Business logic layer |
| `dependencies.py` | Feature-specific FastAPI dependencies |
| `tests/` | Feature-specific tests |

## Feature Registration

Features are registered in `main.py`:

```python
from fastapi import FastAPI
from features.users.routes import router as users_router
from features.products.routes import router as products_router

feature = FastAPI()

feature.include_router(users_router, prefix="/users", tags=["users"])
feature.include_router(products_router, prefix="/products", tags=["products"])
```

## Future Considerations

- [ ] Feature auto-discovery (optional, for convenience)
- [ ] Base service class with common CRUD operations
- [ ] Caching layer (Redis)
- [ ] Background tasks (ARQ or Celery)
- [ ] API versioning strategy
- [ ] WebSocket support patterns
- [ ] Event system for cross-feature communication

## Dependencies

### Runtime Dependencies

```
fastapi
uvicorn[standard]
sqlalchemy[asyncio]
alembic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
structlog
typer
httpx
```

### Development Dependencies

```
pytest
pytest-asyncio
ruff
mypy
pre-commit
```

---

## Development Tooling

### Package Manager: uv

[uv](https://github.com/astral-sh/uv) replaces pip, pip-tools, and venv. Fast, written in Rust.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project with uv
uv init myproject
cd myproject
uv add fastapi sqlalchemy[asyncio]
uv add --dev pytest ruff mypy

# Run commands
uv run pytest
uv run python main.py
```

### Code Quality: Ruff

[Ruff](https://github.com/astral-sh/ruff) replaces Black, isort, Flake8, and more. Single tool for formatting and linting.

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "SIM",    # flake8-simplify
]

[tool.ruff.format]
quote-style = "double"
```

### Type Checking: mypy

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

### Testing: pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests", "features"]
```

### Tooling Summary

| Category | Tool | Replaces |
|----------|------|----------|
| Package manager | **uv** | pip, pip-tools, venv, poetry |
| Formatter | **Ruff** | Black, isort |
| Linter | **Ruff** | Flake8, pylint, pyupgrade |
| Type checker | **mypy** | - |
| Git hooks | **pre-commit** | manual checks |
| Testing | **pytest** | unittest |

## Open Questions

1. Should features be self-contained packages or just directories?
2. How to handle cross-feature dependencies elegantly?
3. Should we provide a base CRUD service/repository pattern?
4. Feature-level vs global middleware?
5. How to handle feature-specific settings?

---

## Implementation Plan

### Phase 1: Foundation

**1.1 Project Setup**
- Initialize Python package structure with `pyproject.toml` (uv-compatible)
- Use uv for package management
- Set up development tools (ruff, mypy, pre-commit)
- Configure pytest with async support
- Create basic CI/CD pipeline (GitHub Actions)

**1.2 Configuration System**
- Implement `Settings` class using Pydantic Settings
- Support for `.env` files and environment variables
- Settings validation at startup
- Typed access to configuration values

**1.3 Database Core**
- Async SQLAlchemy engine and session factory
- `BaseModel` with `id`, `created_at`, `updated_at`
- Database dependency for FastAPI (`get_db`)
- Alembic setup with async support
- CLI commands: `db migrate`, `db upgrade`, `db downgrade`

**1.4 Featurelication Factory**
- `create_feature()` function for FastAPI instance creation
- Lifespan management (startup/shutdown)
- Exception handlers registration
- Middleware registration

### Phase 2: Core Features

**2.1 Logging & Observability**
- structlog configuration
- Request ID middleware
- Request/response logging middleware
- Correlation ID propagation

**2.2 Authentication**
- JWT token utilities (create, verify, refresh)
- Password hashing utilities
- `get_current_user` dependency
- OAuth2 password flow implementation

**2.3 Authorization**
- Permission checker dependency
- Role-based access control
- Decorator for route protection

**2.4 Shared Utilities**
- Pagination dependency and schemas
- Standard response schemas (success, error, list)
- Common exceptions (NotFound, Forbidden, etc.)

### Phase 3: Feature System

**3.1 Feature Structure**
- Define feature conventions and file structure
- Create feature template/scaffold
- Feature configuration class

**3.2 Feature Registration**
- Router auto-discovery (optional)
- Feature initialization hooks
- Model discovery for Alembic

**3.3 Example Feature: Users**
- Complete implementation as reference
- User model, schemas, routes, services
- Registration, login, profile endpoints
- Full test coverage

### Phase 4: Developer Experience

**4.1 CLI Tooling**
- `paxx bootstrap <project>` - Create new uv-compatible project (generates plain code, no wrfeatureers)
- `paxx feature create <name>` - Generate new domain feature from template
- `paxx start` - Development server (thin wrfeatureer around uvicorn)
- `paxx db` - Database commands (thin wrfeatureer around alembic)
- `paxx shell` - Interactive shell with feature context

**4.2 Testing Utilities**
- Test client factory
- Database fixtures (test DB, transactions)
- Authentication helpers for tests
- Factory classes for models

**4.3 Documentation**
- Getting started guide
- Feature structure conventions
- API reference
- Example project

### Phase 5: Advanced Features (Future)

**5.1 Caching**
- Redis integration
- Cache decorator
- Cache invalidation patterns

**5.2 Background Tasks**
- Task queue integration (ARQ/Celery)
- Task decorator
- Scheduled tasks

**5.3 Events**
- In-process event bus
- Cross-feature communication
- Event handlers in features

**5.4 WebSockets**
- WebSocket manager
- Room/channel patterns
- Authentication for WebSockets

---

## Milestones

| Milestone | Phases | Goal |
|-----------|--------|------|
| **M1: Bootable** | 1.1 - 1.4 | Can create and run a FastAPI feature with DB |
| **M2: Secure** | 2.1 - 2.4 | Auth, logging, and shared utilities work |
| **M3: Structured** | 3.1 - 3.3 | Feature system with working example |
| **M4: Usable** | 4.1 - 4.3 | CLI tools and testing utilities |
| **M5: Complete** | 5.x | Advanced features as needed |

## Implementation Notes

- Each phase should have tests before moving to the next
- Keep dependencies minimal - add only when needed
- Document decisions in ADRs (Architecture Decision Records)
- Create example project alongside framework development
- Prioritize developer ergonomics over cleverness
- **No wrfeatureer libraries** - Generate plain code using libraries directly
- **Scaffolding featureroach** - CLI generates code, user owns it

---

## Developer Workflow

### Installation

```bash
pip install paxx
```

### Create a New Project

```bash
paxx bootstrap myproject
cd myproject
```

This generates:

```
myproject/
├── main.py                     # Featurelication entry point
├── settings.py                 # Pydantic Settings configuration
├── features/                       # Domain features go here
│   └── .gitkeep
├── core/                       # Core utilities
│   ├── __init__.py
│   ├── database.py
│   ├── security.py
│   ├── exceptions.py
│   ├── dependencies.py
│   └── schemas.py
├── migrations/                 # Alembic migrations
│   ├── versions/
│   └── env.py
├── tests/
│   └── conftest.py
├── .env.example
├── .gitignore
└── pyproject.toml
```

### Create Domain Features

```bash
paxx feature create users
paxx feature create products
paxx feature create orders
```

Each command generates a new feature under `features/`:

```
features/users/
├── __init__.py
├── routes.py
├── models.py
├── schemas.py
├── services.py
├── dependencies.py
└── tests/
    ├── __init__.py
    └── test_routes.py
```

### Daily Development Commands

```bash
# Start development server (with auto-reload)
uv run paxx start

# Database operations
uv run paxx db migrate "add users table"    # Create migration
uv run paxx db upgrade                       # Featurely migrations
uv run paxx db downgrade                     # Rollback last migration
uv run paxx db status                        # Show migration status

# Interactive shell with feature context loaded
uv run paxx shell

# Run tests
uv run pytest                                 # Framework fixtures auto-loaded
uv run pytest features/users/                     # Test specific feature
```

### Example: Building a Feature

```bash
# 1. Create a new feature
uv run paxx feature create blog

# 2. Define your model in features/blog/models.py
# 3. Create migration
uv run paxx db migrate "create posts table"
uv run paxx db upgrade

# 4. Implement schemas, services, routes
# 5. Register router in main.py
# 6. Start and test
uv run paxx start
```

### Project Configuration

Settings are managed via environment variables and `.env` file:

```python
# settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    feature_name: str = "My Feature"
    debug: bool = False
    database_url: str
    secret_key: str

    class Config:
        env_file = ".env"
```

---

## Framework Design Featureroach

**Scaffolding + Conventions (No Wrfeatureers)**

paxx is **not** a library with wrfeatureer abstractions. It's a scaffolding tool that generates plain code using well-known libraries directly.

### What paxx Is

| paxx Provides | How |
|----------------|-----|
| Project scaffolding | `paxx bootstrap` generates starter code |
| Feature scaffolding | `paxx feature create` generates domain features |
| CLI utilities | `paxx db`, `paxx start`, `paxx shell` |
| Conventions | Consistent structure and patterns |
| Curated stack | Tested combinations of libraries |

### What paxx Is NOT

| paxx Does NOT | Instead |
|----------------|---------|
| Provide wrfeatureer libraries | Use FastAPI, SQLAlchemy, Pydantic directly |
| Hide implementation details | All generated code is visible and editable |
| Enforce patterns | Conventions are recommended, not required |

### Generated Code Uses Libraries Directly

```python
# Generated core/database.py - uses SQLAlchemy directly
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# NOT: from paxx.db import Base  (no wrfeatureers!)
```

```python
# Generated core/security.py - uses python-jose directly
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

# NOT: from paxx.security import create_access_token  (no wrfeatureers!)
```

### Similar Featureroaches (Prior Art)

This pattern is well-established:

| Tool | Featureroach |
|------|----------|
| **Cookiecutter Django** | Generates project, no runtime dependency |
| **Create React Feature** | Scaffolds, then "eject" to own code |
| **Vite** | Project templates, direct library usage |
| **FastAPI Project Generator** | Official templates, you own the code |
| **Rails generators** | `rails generate` creates plain Ruby files |

### Benefits

- **Debuggable** - No hidden framework code to trace through
- **Learnable** - See exactly how everything works
- **Upgradeable** - Update SQLAlchemy, FastAPI directly
- **Customizable** - Modify any file without fighting abstractions

### paxx as Runtime Dependency

paxx is included as a dependency in generated projects to provide CLI commands for daily development:

```bash
uv run paxx feature create <name>  # Generate new domain features
uv run paxx db migrate "..."  # Wrfeatureer around alembic (convenience)
uv run paxx db upgrade        # Wrfeatureer around alembic (convenience)
uv run paxx start             # Wrfeatureer around uvicorn (convenience)
uv run paxx shell             # Interactive shell with feature context
```

These are **thin wrfeatureers for convenience**, not abstractions. They call the underlying tools directly.

---

## paxx Package Structure

paxx itself is minimal — CLI commands and templates. It serves as both a scaffolding tool and a runtime dependency for generated projects.

```
paxx/
├── cli/
│   ├── __init__.py
│   ├── main.py              # Typer feature entry point
│   ├── bootstrap.py         # `paxx bootstrap` - project scaffolding
│   ├── feature.py           # `paxx feature` - feature management
│   ├── db.py                # `paxx db` - wraps alembic commands
│   ├── start.py             # `paxx start` - wraps uvicorn
│   └── shell.py             # `paxx shell` - interactive shell
├── templates/
│   ├── project/             # Project template files
│   │   ├── main.py.jinja
│   │   ├── settings.py.jinja
│   │   ├── pyproject.toml.jinja
│   │   ├── core/
│   │   │   ├── database.py.jinja
│   │   │   ├── security.py.jinja
│   │   │   └── exceptions.py.jinja
│   │   ├── core/
│   │   ├── migrations/
│   │   └── tests/
│   └── feature/                 # Feature template files
│       ├── __init__.py.jinja
│       ├── routes.py.jinja
│       ├── models.py.jinja
│       ├── schemas.py.jinja
│       ├── services.py.jinja
│       ├── dependencies.py.jinja
│       └── tests/
├── utils/
│   └── templating.py        # Jinja2 template rendering
└── __init__.py
```

### What paxx Actually Contains

| Component | Purpose | Lines of Code (est.) |
|-----------|---------|---------------------|
| CLI commands | Typer commands for scaffolding and convenience wrfeatureers | ~300 |
| Template rendering | Jinja2 logic to generate files | ~100 |
| Templates | Project and feature file templates | ~500 (template content) |

**Total: ~400 lines of Python + templates**

### Custom Code That Gets Generated

These are non-trivial pieces that paxx generates (not wraps):

**1. Alembic `env.py`** - Async-compatible, auto-discovers models from features:
```python
# Generated: migrations/env.py
from core.database import Base
from pathlib import Path
import importlib

# Auto-discover models from all features
for feature_dir in Path("features").iterdir():
    if (feature_dir / "models.py").exists():
        importlib.import_module(f"features.{feature_dir.name}.models")

target_metadata = Base.metadata
```

**2. Test fixtures** - Working async fixtures in `conftest.py`:
```python
# Generated: tests/conftest.py
@pytest.fixture
async def db_session():
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    def override_get_db():
        yield db_session
    feature.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(feature=feature, base_url="http://test") as client:
        yield client
```

### What paxx Does NOT Contain

| Not Included | Use Instead |
|--------------|-------------|
| ORM base classes | SQLAlchemy `DeclarativeBase` directly |
| Auth utilities | python-jose, passlib directly |
| Validation helpers | Pydantic directly |
| HTTP client | httpx directly |
| Logging setup | structlog directly |
| Runtime library imports | Generated code imports libraries directly, not paxx wrfeatureers |
