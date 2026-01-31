# CLI Reference

## Global Options

### `paxx --version`

Show the paxx version and exit.

```bash
paxx --version
paxx -v
```

---

## Project Commands

### `paxx bootstrap`

Create a new paxx project with the standard structure.

```bash
paxx bootstrap <name> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the new project. Use `.` to bootstrap in current directory. |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output-dir PATH` | Directory to create the project in | Current directory |
| `-d, --description TEXT` | Project description | - |
| `-a, --author TEXT` | Author name | "Author" |
| `-f, --force` | Skip confirmation prompts (CI-friendly) | False |

**Examples:**

```bash
paxx bootstrap myproject
paxx bootstrap my-api --description "My awesome API"
paxx bootstrap myproject -o /path/to/projects
paxx bootstrap .                    # Bootstrap in current directory
paxx bootstrap myproject --force    # Non-interactive mode
```

---

### `paxx start`

Start the development server (uvicorn wrapper).

```bash
paxx start [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-h, --host TEXT` | Host to bind to | 127.0.0.1 |
| `-p, --port INTEGER` | Port to bind to | 8000 |
| `-r, --reload / -R, --no-reload` | Enable auto-reload | Enabled |
| `-w, --workers INTEGER` | Number of workers (only without reload) | 1 |

**Examples:**

```bash
paxx start                         # Start on localhost:8000 with reload
paxx start --port 3000             # Start on port 3000
paxx start --host 0.0.0.0          # Bind to all interfaces
paxx start --no-reload --workers 4 # Production-like mode
```

---

## Feature Commands

### `paxx feature create`

Create a new domain feature from scratch.

```bash
paxx feature create <name> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the new feature (required) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --description TEXT` | Feature description | - |

**Examples:**

```bash
paxx feature create users
paxx feature create blog_posts
paxx feature create orders --description "Order management"
```

**Generated Structure:**

```
features/<name>/
├── __init__.py
├── config.py      # Feature configuration (prefix, tags)
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── services.py    # Business logic
└── routes.py      # API endpoints
```

---

### `paxx feature add`

Add a bundled feature to your project.

```bash
paxx feature add <feature> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `feature` | Name of the bundled feature to add (required) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --force` | Overwrite existing feature | False |

**Available Features:**

| Feature | Description |
|---------|-------------|
| `example_products` | Complete CRUD example with e2e tests |

**Examples:**

```bash
paxx feature add example_products  # Add the example CRUD feature
paxx feature add auth --force      # Overwrite existing auth feature
```

When a bundled feature is added:
1. Files are copied to `features/<name>/`
2. E2E tests are copied to `e2e/`
3. Router is automatically registered in `main.py`

---

### `paxx feature list`

List all available bundled features.

```bash
paxx feature list
```

---

## Database Commands

All database commands are wrappers around Alembic.

### `paxx db migrate`

Create a new database migration.

```bash
paxx db migrate <message> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `message` | Migration message describing the changes (required) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-a, --autogenerate / -A, --no-autogenerate` | Auto-detect model changes | Enabled |

**Examples:**

```bash
paxx db migrate "add users table"
paxx db migrate "add email index" --no-autogenerate
```

---

### `paxx db upgrade`

Apply migrations to the database.

```bash
paxx db upgrade [REVISION]
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `revision` | Target revision | head (latest) |

**Examples:**

```bash
paxx db upgrade          # Apply all pending migrations
paxx db upgrade head     # Same as above
paxx db upgrade +1       # Apply next migration only
paxx db upgrade abc123   # Migrate to specific revision
```

---

### `paxx db downgrade`

Revert migrations.

```bash
paxx db downgrade [REVISION]
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `revision` | Target revision | -1 (previous) |

**Examples:**

```bash
paxx db downgrade        # Revert last migration
paxx db downgrade -1     # Same as above
paxx db downgrade -2     # Revert last 2 migrations
paxx db downgrade base   # Revert all migrations
paxx db downgrade abc123 # Downgrade to specific revision
```

---

### `paxx db status`

Show current migration status.

```bash
paxx db status
```

---

### `paxx db history`

Show migration history.

```bash
paxx db history [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show detailed history |

---

### `paxx db heads`

Show current available heads (useful for migration branches).

```bash
paxx db heads
```

---

## Docker Commands

Docker Compose wrappers for development.

### `paxx docker up`

Start the development environment.

```bash
paxx docker up [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-d, --detach` | Run containers in the background | False |
| `-b, --build` | Rebuild images before starting | False |

**Examples:**

```bash
paxx docker up           # Start in foreground (see logs)
paxx docker up -d        # Start in background
paxx docker up --build   # Rebuild and start
```

---

### `paxx docker down`

Stop the development environment.

```bash
paxx docker down [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-v, --volumes` | Remove named volumes (deletes database data) | False |

**Examples:**

```bash
paxx docker down         # Stop containers, keep data
paxx docker down -v      # Stop and delete all data
```

---

### `paxx docker build`

Build the Docker images.

```bash
paxx docker build [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--no-cache` | Build without using cache | False |

**Examples:**

```bash
paxx docker build            # Build with cache
paxx docker build --no-cache # Full rebuild
```

---

### `paxx docker logs`

Show container logs.

```bash
paxx docker logs [OPTIONS] [SERVICE]
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `service` | Service to show logs for (app, db) | All services |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --follow / -F, --no-follow` | Follow log output | Follow |

**Examples:**

```bash
paxx docker logs         # Follow all logs
paxx docker logs app     # Follow app logs only
paxx docker logs -F      # Show logs without following
```

---

### `paxx docker ps`

Show running containers.

```bash
paxx docker ps
```

---

### `paxx docker exec`

Execute a command in a running container.

```bash
paxx docker exec [SERVICE] [COMMAND]
```

**Arguments:**

| Argument | Description | Default |
|----------|-------------|---------|
| `service` | Service to run command in | app |
| `command` | Command to execute | bash |

**Examples:**

```bash
paxx docker exec              # Open bash in app container
paxx docker exec app bash     # Same as above
paxx docker exec db psql      # Open psql in database container
```

---

## Infrastructure Commands

Add cross-cutting infrastructure components.

### `paxx infra add`

Add an infrastructure component to your project.

```bash
paxx infra add <name> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the infrastructure component |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --force` | Overwrite existing files | False |

**Available Components:**

| Component | Description |
|-----------|-------------|
| `redis` | Redis caching with async support |
| `storage` | Object storage (S3/MinIO/local) |
| `metrics` | Prometheus metrics and OpenTelemetry tracing |

**Examples:**

```bash
paxx infra add redis     # Add Redis caching
paxx infra add storage   # Add object storage
paxx infra add metrics   # Add observability
```

When an infrastructure component is added:
1. Templates are rendered to `services/`
2. Docker service is merged into `docker-compose.yml`
3. Dependencies are added to `pyproject.toml`
4. Environment variables are added to `settings.py` and `.env.example`

See [Infrastructure](infrastructure.md) for detailed usage.

---

### `paxx infra list`

List available infrastructure components.

```bash
paxx infra list
```

---

## Extension Commands

Extensions are add-ons that enhance existing infrastructure components. Unlike infrastructure components, they don't add new services but extend functionality of existing ones.

### `paxx ext add`

Add an extension to your project.

```bash
paxx ext add <name> [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `name` | Name of the extension to add |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --force` | Overwrite existing files | False |

**Available Extensions:**

| Extension | Description | Requires |
|-----------|-------------|----------|
| `arq` | Background task queue with ARQ | redis |
| `websocket` | WebSocket connections with room support | (optional redis) |
| `postgis` | PostGIS geospatial extension | - |

**Examples:**

```bash
paxx ext add arq         # Add ARQ task queue (requires redis)
paxx ext add websocket   # Add WebSocket support
paxx ext add postgis     # Add PostGIS to postgres
```

When an extension is added:
1. Templates are rendered to `services/`
2. Dependencies are added to `pyproject.toml`
3. Environment variables are added to `settings.py` and `.env.example`

See [Extensions](extensions.md) for detailed usage.

---

### `paxx ext list`

List available extensions.

```bash
paxx ext list
```

---

## Deployment Commands

Generate deployment configurations.

### `paxx deploy add`

Add a deployment configuration to your project.

```bash
paxx deploy add <type>
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `type` | Deployment type to add |

**Available Types:**

| Type | Description |
|------|-------------|
| `linux-server` | Traefik + Docker + systemd with SSL |

**Examples:**

```bash
paxx deploy add linux-server
```

When a deployment is added:
1. Configuration files are created in `deploy/<type>/`
2. GitHub Actions workflow is created at `.github/workflows/build.yml`

**Generated Files (linux-server):**

```
deploy/linux-server/
├── deploy.sh              # Main deployment script
├── deploy-init.sh         # Initial server setup
├── deploy-if-changed.sh   # Deploy only if image changed
├── deploy-purge.sh        # Clean up deployment
├── get-status.sh          # Check deployment status
├── server-setup.sh        # Server configuration
├── docker-compose.yml     # Production compose file
├── traefik-dynamic.yml    # Traefik routing config
├── .env.example           # Production env template
├── README.md              # Deployment documentation
└── certs/                 # TLS certificates directory

.github/workflows/
└── build.yml              # CI/CD pipeline
```

See [Deployment](deployment.md) for detailed setup instructions.
