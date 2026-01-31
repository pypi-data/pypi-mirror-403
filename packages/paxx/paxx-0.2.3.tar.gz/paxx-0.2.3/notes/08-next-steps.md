# Next Steps: Deployment-Ready Apps

## The Insight

Infrastructure services have different lifecycles than the app:

- **App**: Deploy on every release, ephemeral containers, easy rollback
- **Database**: Provision once, persistent, migrated carefully, never redeployed
- **Redis/Cache**: Provision once, may be ephemeral or persistent depending on use

Paxx should not try to orchestrate all of this. Cloud platforms (Fly, AWS, Railway) already handle provisioning databases better than a CLI tool ever could.

---

## Philosophy: Deployment-Ready, Not Deployment-Managing

> **Paxx scaffolds apps that are trivially deployable. The user picks their platform and provisions infrastructure there.**

The Dockerfile is the universal interface. Every platform knows how to run a container. Paxx generates one good Dockerfile and lets you take it anywhere.

---

## What Paxx Should Do

### 1. 12-Factor App Compliance

The generated app separates config from code via environment variables. This is the key thing that makes apps deployable *anywhere*.

- `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY` all come from env
- No hardcoded hosts, ports, or credentials
- Settings validated at startup with Pydantic

### 2. Production Dockerfile

A well-crafted multi-stage Dockerfile that works on any container platform:

```dockerfile
# Build stage
FROM python:3.12-slim as builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# Runtime stage
FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "4"]
```

This works on Fly, ECS, Cloud Run, Kubernetes, or any VPS with Docker.

### 3. Health Check Endpoint

Already wired up at `/health` for platform readiness/liveness probes:

```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 4. Graceful Shutdown

Proper signal handling so containers can be killed cleanly:

```python
@app.on_event("shutdown")
async def shutdown():
    # Close DB connections, finish in-flight requests
    await engine.dispose()
```

### 5. Migrations as a Separate Concern

Migrations should run *before* deploy, not during container startup:

```bash
# In CI/CD pipeline, before deploying new containers:
uv run alembic upgrade head

# Or as a one-off command on the platform:
fly ssh console -C "uv run alembic upgrade head"
```

Container startup should be fast and idempotent. Mixing migrations into startup creates race conditions with multiple replicas.

### 6. Documentation (DEPLOY.md)

A generated `DEPLOY.md` explaining concepts and common patterns:

- What environment variables are required
- How to run migrations
- Example commands for popular platforms (Fly, Railway, ECS)
- How to set up a database (links to platform docs, not automation)

---

## What Paxx Should NOT Do

- **Wrap platform CLIs** (`fly deploy`, `aws ecs`, etc.) - they're already good
- **Provision infrastructure** (databases, Redis, queues) - platforms do this better
- **Generate platform-specific configs** (fly.toml, task definitions) - these change frequently and are well-documented by the platforms themselves
- **Detect services and orchestrate them** - over-engineering for a scaffolder

---

## 12-Factor Analysis: Current State

| Factor | Name | Status | Notes |
|--------|------|--------|-------|
| I | Codebase | ✅ Done | Git-ready with .gitignore |
| II | Dependencies | ✅ Done | pyproject.toml + uv.lock, explicit and isolated |
| III | Config | ✅ Done | Pydantic Settings, all config from env vars |
| IV | Backing Services | ✅ Done | DATABASE_URL as attached resource |
| V | Build/Release/Run | ✅ Done | Production Dockerfile exists |
| VI | Processes | ✅ Done | Stateless request handling, no sticky sessions |
| VII | Port Binding | ✅ Done | Uvicorn self-contained, no external server needed |
| VIII | Concurrency | ✅ Done | Dockerfile has `--workers 4`, documented in DEPLOY.md |
| IX | Disposability | ✅ Done | Startup validates DB, graceful shutdown, health checks |
| X | Dev/Prod Parity | ✅ Done | docker-compose uses Postgres |
| XI | Logs | ✅ Done | structlog configured, JSON/console output to stdout |
| XII | Admin Processes | ✅ Done | DEPLOY.md documents migrations, scaling, health checks |

All 12 factors complete.

---

## Implementation Plan

### Already Done
- [x] Full project scaffolding (`paxx bootstrap`)
- [x] Feature system (`paxx feature create`, `paxx feature add`)
- [x] Dev server (`paxx start`)
- [x] Database migrations (`paxx db`)
- [x] Settings via environment variables (12-factor)

### To Do

#### Phase 1: Docker Templates
- [x] Create `Dockerfile.jinja` (production multi-stage build)
- [x] Create `Dockerfile.dev.jinja` (dev with hot-reload, mounted volumes)
- [x] Create `docker-compose.yml.jinja` (local dev: app + Postgres)
- [x] Create `.dockerignore.jinja`
- [x] Docker setup with PostgreSQL

#### Phase 2: 12-Factor Compliance
- [x] Configure structured logging (structlog to stdout, JSON format)
- [x] Add `log_level` and `log_format` to settings
- [x] Improve `/health` endpoint (verify DB connectivity, return 503 if unhealthy)
- [x] Add startup validation (fail fast if DB unreachable)
- [x] Add graceful shutdown handler (already partially done)

#### Phase 3: Production Readiness
- [x] Create `DEPLOY.md.jinja` with deployment guidance
- [x] Document migration strategy (run before deploy, not in container startup)
- [x] Document concurrency (`uvicorn --workers`)

#### Phase 4: Dev Experience Polish
- [x] `paxx docker up` convenience command (thin wrapper around docker compose)
- [x] Ensure hot-reload works in Docker dev container

---

## Design Decision: Docker-First

Single mode with Docker and PostgreSQL:

```bash
paxx bootstrap myproject           # Docker, PostgreSQL, production-ready
```

**What you get:**
- Docker dev environment
- PostgreSQL in docker-compose
- Production Dockerfile
- Health endpoint

The generated code is *theirs* - they can swap Postgres for SQLite or customize the setup as needed. That's the escape hatch.

---

## Notes

**Why this approach:**
- Paxx stays focused on scaffolding, not deployment orchestration
- Users learn their platform instead of learning paxx's abstractions
- Less maintenance burden - no need to track every platform's API changes
- The Dockerfile is the universal interface that works everywhere
