# Next Steps

## deploy-purge.sh improvements

### Package removal considerations

The purge script currently removes `jq` and `curl`. Other packages installed by `server-setup.sh` are intentionally left because they're often pre-installed:

| Package | Ubuntu | Debian | Raspberry Pi OS | Action |
|---------|--------|--------|-----------------|--------|
| `jq` | ❌ | ❌ | ❌ | Remove |
| `curl` | ❌ | ❌ | ❌ | Remove |
| `ufw` | ✅ | ❌ | ❌ | Keep (risky) |
| `ca-certificates` | ✅ | ⚠️ | ✅ | Keep |
| `gnupg` | ✅ | ✅ | ✅ | Keep |
| `lsb-release` | ✅ | ✅ | ✅ | Keep |

**Future improvement:** Consider a manifest-based approach where `server-setup.sh` records which packages it actually installed (vs already present), and `deploy-purge.sh` only removes those. This would handle `ufw` correctly across distros.

---

update status script so that it includes currently running image hash
+ ideally last deployment timestamp
maybe there could be time in logs?

support claude in github - github actions - check `/install-github-app`

endpoint for telemetry

focus on review and documentation
- review paxx project
- review generated project

add ai (claude?) files to make the project ai-first.

make linux deployment raspi-optimised

briefly check other deployment types

---

This is for a paxx-bootstrapped app:

## paxx-test-app Review Suggestions

### High Priority

1. **Expand test coverage** - Only the health endpoint is tested
   - Add unit tests for core modules (exceptions, middleware, dependencies)
   - Create integration tests with test database isolation
   - Add `pytest-cov` for coverage reporting
   - Target: 80%+ coverage for core modules

2. **Activate pre-commit hooks** - Dependency exists but config missing
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

3. **Enforce secret key in production** - Currently just logs a warning
   ```python
   # settings.py - should fail hard in production
   if settings.is_production and "CHANGE_ME" in settings.secret_key:
       raise ValueError("Must set SECRET_KEY in production")
   ```

4. **Add CI linting/testing workflow** - build.yml only builds Docker images
   - Add separate workflow for PRs with lint + test steps
   - Run tests before allowing merge

### Medium Priority

5. **Add security headers middleware** - Missing standard security headers
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY
   - X-XSS-Protection: 1; mode=block
   - Strict-Transport-Security (for HTTPS)

6. **Add rate limiting** - Consider `slowapi` for API rate limiting

7. **Add a Makefile** - Common commands improve DX
   ```makefile
   dev:
       uv run uvicorn main:app --reload
   test:
       uv run pytest
   lint:
       uv run ruff check . --fix
   migrate:
       uv run alembic upgrade head
   ```

8. **Document /docs endpoint** - FastAPI auto-generates Swagger UI but README doesn't mention it

### Low Priority

9. **Add metrics endpoint** - Prometheus-compatible `/metrics` for production monitoring

10. **API versioning strategy** - Consider `/api/v1/` prefix for future compatibility

11. **Add database schema documentation** - ERD diagrams for complex schemas

12. **Add Architecture Decision Records (ADRs)** - Document key technical decisions

---

## AI-First Documentation (Claude Code / Cursor / Copilot)

To make the project optimally understandable by AI coding assistants, add the following:

### 1. CLAUDE.md (Root Level)

Primary context file for Claude Code. Should contain:

# Project Overview

paxx-test-app is a FastAPI application scaffolded with the paxx framework.

## Tech Stack
- Python 3.12+
- FastAPI (async web framework)
- SQLAlchemy 2.0 (async ORM)
- Alembic (migrations)
- PostgreSQL (production) / SQLite (development)
- Structlog (structured logging)
- Pydantic v2 (validation)

## Project Structure

```bash
├── main.py              # App factory, lifespan management
├── settings.py          # Pydantic settings (env vars)
├── core/                # Cross-cutting concerns
│   ├── dependencies.py  # FastAPI dependencies
│   ├── exceptions.py    # Custom exceptions + handlers
│   ├── logging.py       # Structlog configuration
│   ├── middleware.py    # Request ID, timing middleware
│   └── schemas.py       # Base Pydantic schemas
├── db/                  # Database layer
│   ├── database.py      # SQLAlchemy setup, Base models
│   └── migrations/      # Alembic migrations
├── features/            # Domain features (add new features here)
│   └── health/          # Reference feature implementation
└── e2e/                 # End-to-end tests
```

## Key Patterns

### Adding a New Feature
1. Create `features/<name>/` directory
2. Add: models.py, schemas.py, services.py, routes.py
3. Register router in main.py: `app.include_router(router, prefix="/<name>")`
4. Create migration: `uv run alembic revision --autogenerate -m "Add <name>"`

### Database Models
All models inherit from `BaseModel` which provides:
- `id`: Auto-increment primary key
- `created_at`: Server-side timestamp
- `updated_at`: Auto-updated timestamp

### Exception Handling
Use custom exceptions from `core/exceptions.py`:
- `NotFoundError(message, detail?)` → 404
- `BadRequestError(message, detail?)` → 400
- `UnauthorizedError(message, detail?)` → 401
- `ForbiddenError(message, detail?)` → 403
- `ConflictError(message, detail?)` → 409

### Configuration
All settings via environment variables or `.env` file.
See `.env.example` for available options.

## Common Commands
```bash
uv run uvicorn main:app --reload  # Dev server
uv run alembic upgrade head       # Run migrations
uv run pytest                     # Run tests
uv run ruff check . --fix         # Lint
uv run mypy .                     # Type check
```

## Testing
- E2E tests in `e2e/` directory
- Use `AsyncClient` from httpx for API tests
- Tests run with: `uv run pytest`

### 2. .cursorrules / .cursor/rules (For Cursor IDE)

You are working on a FastAPI application using Python 3.12+.

Key conventions:
- Use async/await for all database operations
- Use dependency injection via FastAPI's Depends()
- All API responses use Pydantic schemas from core/schemas.py
- Custom exceptions go in core/exceptions.py
- New features go in features/<name>/ with models, schemas, services, routes
- Use structlog for logging, not print() or stdlib logging
- Database models inherit from db.database.BaseModel
- Settings accessed via settings.py, never hardcoded

When creating new endpoints:
1. Define Pydantic request/response schemas
2. Create service functions for business logic
3. Keep routes thin - delegate to services
4. Use appropriate HTTP status codes
5. Handle errors with custom exceptions

Testing:
- Write async tests using pytest-asyncio
- Use httpx.AsyncClient for API tests
- Tests go in e2e/ directory


### 3. .github/copilot-instructions.md (For GitHub Copilot)

Similar content to CLAUDE.md but in Copilot's expected format.

### 4. Architecture Documentation

Create `docs/architecture.md`:
- System overview diagram (Mermaid)
- Request flow through middleware → routes → services → database
- Feature module structure
- Database schema relationships

### 5. Code Comments for AI Context

Add module-level docstrings explaining purpose:
```python
"""
core/middleware.py

HTTP middleware for cross-cutting concerns:
- RequestIDMiddleware: Adds X-Request-ID header for request tracing
- TimingMiddleware: Adds X-Process-Time header for performance monitoring

Middleware is registered in main.py in reverse execution order.
"""
```

### 6. Example Feature Template

Create `features/_template/` with:
- models.py (example model with relationships)
- schemas.py (CRUD schemas)
- services.py (business logic patterns)
- routes.py (REST endpoint patterns)
- tests/ (test patterns)

This serves as copy-paste reference for AI and developers.

### 7. .aiexclude / .claudeignore

List files AI should ignore:

```
uv.lock
*.pyc
__pycache__/
.env
*.log
```

### 8. Decision Log

Create `docs/decisions/` with numbered decision records:
- `001-async-sqlalchemy.md` - Why async SQLAlchemy 2.0
- `002-structlog.md` - Why structlog over stdlib logging
- `003-feature-structure.md` - Why domain-driven feature folders

This helps AI understand *why* patterns exist, not just *what* they are.

### Summary: Files to Add

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Primary AI context (Claude Code) |
| `.cursorrules` | Cursor IDE instructions |
| `.github/copilot-instructions.md` | GitHub Copilot context |
| `docs/architecture.md` | System diagrams and flows |
| `features/_template/` | Reference implementation |
| `.aiexclude` | Files to ignore |
| `docs/decisions/` | Architecture Decision Records |
