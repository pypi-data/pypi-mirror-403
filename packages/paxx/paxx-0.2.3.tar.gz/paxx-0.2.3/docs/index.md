# paxx

A domain-oriented FastAPI project scaffolding CLI.

paxx generates production-ready code using well-known libraries (FastAPI, SQLAlchemy async, Pydantic v2, Alembic) directly. No wrapper abstractions, no framework lock-in - just a solid starting point for domain-driven FastAPI applications.

## Why paxx?

Get a well-structured, object-oriented and composable app skeleton that you can build on. Skip the boilerplate setup you've done a hundred times

## Philosophy

- **No magic** - Generated code uses FastAPI, SQLAlchemy, and Pydantic directly
- **No lock-in** - After bootstrapping, your project has zero dependency on paxx
- **Domain-driven** - Features organized by business capability, not technical layer
- **Production-ready** - Includes Docker, migrations, logging, and deployment configs
- **Your code, your rules** - The generated structure is a starting point, not a constraint. Reshape it to fit your needs

## Quick Start

```bash
# Install paxx globally
uv tool install paxx

# Create a new project
paxx bootstrap myproject

# Navigate and start
cd myproject
docker compose up
```

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to see your API documentation.

## What's Generated?

When you run `paxx bootstrap`, you get a fully configured FastAPI project with:

- **Application factory pattern** with async lifespan management
- **Pydantic Settings** for type-safe configuration
- **SQLAlchemy async** with session management and BaseModel
- **Alembic** migrations pre-configured
- **Docker Compose** for local development (app + PostgreSQL)
- **Structured logging** with JSON and console output formats
- **CORS middleware** pre-configured
- **Health check endpoint** out of the box
- **Domain-driven structure** with a `features/` directory for business logic

## Core Concepts

### Features

Features are self-contained domain modules under `features/`. Each feature contains models, schemas, services, and routes for a specific business capability.

```bash
# Create a new feature
paxx feature create users

# Add a bundled feature
paxx feature add example_products
```

### Infrastructure

Add new infrastructure components to your application like databases, caching, and object storage.

```bash
paxx infra add redis      # Redis caching
paxx infra add storage    # Object storage
```

### Extensions

Extensions enhance existing infrastructure or add cross-cutting capabilities without introducing new infrastructure components.

```bash
paxx ext add arq          # Background tasks (requires redis)
```

### Deployment

Generate deployment configurations for different environments.

```bash
# Add Linux server deployment (Traefik + systemd)
paxx deploy add linux-server
```

## Next

[Bootstrap your first project](getting-started.md)
