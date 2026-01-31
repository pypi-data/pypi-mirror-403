# Project Structure

When you run `paxx bootstrap myproject`, the following structure is created:

```
myproject/
├── main.py                  # Application entry point & factory
├── settings.py              # Configuration (Pydantic Settings)
├── conftest.py              # Root pytest fixtures
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Project dependencies
├── Makefile                 # Common development commands
├── .env                     # Environment variables (git-ignored)
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore rules
├── README.md                # Project readme
├── DEPLOY.md                # Deployment documentation
│
├── Dockerfile               # Production container image
├── Dockerfile.dev           # Development container image
├── docker-compose.yml       # Development environment
├── .dockerignore            # Docker build exclusions
│
├── core/                    # Core utilities
│   ├── __init__.py
│   ├── logging.py           # Structured logging configuration
│   ├── exceptions.py        # Custom exceptions & handlers
│   ├── middleware.py        # Custom middleware
│   ├── dependencies.py      # FastAPI dependencies
│   └── schemas.py           # Shared Pydantic schemas
│
├── db/                      # Database
│   ├── __init__.py
│   ├── database.py          # Async SQLAlchemy setup
│   └── migrations/          # Alembic migrations
│       ├── env.py           # Alembic environment
│       ├── script.py.mako   # Migration template
│       └── versions/        # Migration files
│
├── features/                # Domain features
│   └── health/              # Built-in health check
│       ├── __init__.py
│       └── routes.py
│
├── e2e/                     # End-to-end tests
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   └── test_health.py       # Health endpoint tests
│
└── deploy/                  # Deployment configs
    └── README.md            # Instructions for adding deployments
```

This structure is a starting point, not a constraint. Feel free to reorganize directories, rename modules, or reshape the architecture to fit your project's needs. After bootstrapping, the code is entirely yours.

## Key Files

### `main.py`

The application entry point using the factory pattern with async lifespan:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate database connection
    if not await verify_database_connection():
        sys.exit(1)
    yield
    # Shutdown: close connections
    await close_db()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Register middleware
    register_middleware(app)

    # Configure CORS
    app.add_middleware(CORSMiddleware, ...)

    # Register routers
    app.include_router(health_router, tags=["health"])

    return app

app = create_app()
```

### `settings.py`

Type-safe configuration using Pydantic Settings:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # Application
    app_name: str = "myproject"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "console"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/myproject"

    # Security
    secret_key: str = "CHANGE-ME-IN-PRODUCTION-USE-SECRETS-TOKEN"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

settings = Settings()
```

### `db/database.py`

Async SQLAlchemy setup with session management:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### `core/logging.py`

Structured logging with JSON and console output:

```python
from core.logging import configure_logging, get_logger

configure_logging(level="INFO", format="json")
logger = get_logger(__name__)

logger.info("Request processed", user_id=123, status="success")
```

### `core/exceptions.py`

Custom exception classes and handlers:

```python
from core.exceptions import NotFoundError, ValidationError

# Raise custom exceptions in your code
raise NotFoundError("User not found")
raise ValidationError("Invalid email format")
```

### `core/dependencies.py`

FastAPI dependencies for common patterns:

```python
from core.dependencies import get_db, PaginationParams

@router.get("/items")
async def list_items(
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    ...
```

---

## Feature Structure

Each feature in `features/` follows this structure:

```
features/<name>/
├── __init__.py      # Feature exports
├── config.py        # Router configuration
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic schemas
├── services.py      # Business logic
└── routes.py        # API endpoints
```

### `config.py`

Defines the router prefix and OpenAPI tags:

```python
from dataclasses import dataclass, field

@dataclass
class FeatureConfig:
    prefix: str = "/users"
    tags: list[str] = field(default_factory=lambda: ["Users"])
```

### `models.py`

SQLAlchemy models using modern mapped column syntax:

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    name: Mapped[str | None] = mapped_column(String(100))
```

### `schemas.py`

Pydantic schemas for request/response validation:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None

    model_config = {"from_attributes": True}
```

### `services.py`

Business logic layer with async functions:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .schemas import UserCreate

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### `routes.py`

FastAPI router with endpoints delegating to services:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from . import services, schemas

router = APIRouter()

@router.post("/", response_model=schemas.UserResponse, status_code=201)
async def create_user(
    data: schemas.UserCreate,
    db: AsyncSession = Depends(get_db),
):
    return await services.create_user(db, data)

@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    user = await services.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

---

## Directory Conventions

| Directory | Purpose |
|-----------|---------|
| `core/` | Shared utilities, middleware, dependencies, schemas |
| `db/` | Database configuration, models base, migrations |
| `features/` | Domain features (business logic organized by capability) |
| `e2e/` | End-to-end API tests |
| `deploy/` | Deployment configurations (added via `paxx deploy add`) |

---

## Registering Features

### Manual Registration

After creating a feature with `paxx feature create`, register it in `main.py`:

```python
from features.users.routes import router as users_router
from features.users.config import FeatureConfig as UsersConfig

def create_app() -> FastAPI:
    app = FastAPI()

    users_config = UsersConfig()
    app.include_router(
        users_router,
        prefix=users_config.prefix,
        tags=users_config.tags,
    )

    return app
```

### Automatic Registration

When using `paxx feature add` with bundled features, the router is automatically registered in `main.py` using AST parsing.

---

## Environment Variables

Key environment variables configured in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Project name |
| `DEBUG` | Enable debug mode | `false` |
| `ENVIRONMENT` | Environment type | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/console) | `console` |
| `DATABASE_URL` | PostgreSQL connection string | Local postgres |
| `SECRET_KEY` | JWT signing key | Must change in production |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |

## Next Steps

Follow the [Tutorial](tutorial.md) to build a complete feature.

If you already know how to build features, you can skip the tutorial and add the pre-built example:

```bash
uv run paxx feature add example_products
```

This adds a complete products feature with:

- Full CRUD implementation
- E2E tests included
- Automatic router registration