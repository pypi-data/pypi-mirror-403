# Deployment

paxx generates 12-factor apps that are deployable to any container platform. The Dockerfile is the universal interface - every platform knows how to run a container.

## Quick Start

Add a deployment configuration to your project:

```bash
paxx deploy add linux-server
```

This generates deployment scripts, Docker Compose configuration, and a CI/CD pipeline.

---

## Environment Variables

| Variable       | Required | Description                                       |
| -------------- | -------- | ------------------------------------------------- |
| `DATABASE_URL` | Yes      | PostgreSQL connection string                      |
| `SECRET_KEY`   | Yes      | Cryptographic signing key (min 32 chars)          |
| `ENVIRONMENT`  | No       | `development`, `staging`, `production`            |
| `LOG_LEVEL`    | No       | DEBUG, INFO, WARNING, ERROR (default: INFO)       |
| `LOG_FORMAT`   | No       | `json` or `console` (default: json in production) |

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Building the Container

```bash
docker build -t myapp .
```

The generated Dockerfile uses a multi-stage build for minimal image size.

---

## Health Checks

The app exposes `/health` which returns:

- `200 OK` when healthy
- `503 Service Unavailable` when database is unreachable

Configure your platform's liveness/readiness probes to hit this endpoint.

---

## Database Migrations

### Local

```bash
docker compose exec app paxx db upgrade
```

### In Production

Access production environment, eg.:

```bash
# SSH into server
ssh user@server
cd /opt/myapp
```

Execute the same command as during local development:

```bash
docker compose exec app paxx db upgrade
```

### Rollback

```bash
paxx db downgrade       # Revert last migration
paxx db downgrade -2    # Revert last 2 migrations
paxx db downgrade abc123  # Downgrade to specific revision
```

### Backwards-Compatible Migrations

For zero-downtime deploys, migrations should be backwards-compatible:

- Add nullable columns, not required ones
- Add new tables before removing old ones
- Use multi-phase migrations for breaking changes:
  1. Deploy: add new column (nullable)
  2. Backfill data
  3. Deploy: code uses new column
  4. Deploy: remove old column

---

## Linux Server Deployment

Add the deployment configuration:

```bash
paxx deploy add linux-server
```

### Generated Files

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

### Setup Process

1. **Configure environment:**

   ```bash
   cp deploy/linux-server/.env.example deploy/linux-server/.env
   # Edit .env with your production values
   ```

2. **Push to GitHub:**

   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push
   ```

3. **Create a release tag:**

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

   This triggers the GitHub Actions build workflow.

4. **Initial server deployment:**
   ```bash
   ./deploy/linux-server/deploy-init.sh user@your-server
   ```

### Architecture

The linux-server deployment uses:

- **Traefik** - Reverse proxy with automatic HTTPS
- **Docker Compose** - Container orchestration
- **systemd** - Process management and auto-restart
- **GitHub Actions** - CI/CD pipeline

### Server Requirements

- Ubuntu 22.04+ or Debian 12+
- Docker and Docker Compose installed
- SSH access with key-based authentication
- Domain name pointing to server IP

### TLS Certificates

Place your certificates in `deploy/linux-server/certs/`:

```
certs/
├── cert.pem      # Full certificate chain
└── key.pem       # Private key
```

Or use Let's Encrypt with Traefik's automatic certificate management.

### Deployment Commands

```bash
# Initial deployment to a new server
./deploy/linux-server/deploy-init.sh user@server

# Standard deployment (pulls and restarts)
./deploy/linux-server/deploy.sh user@server

# Deploy only if image has changed
./deploy/linux-server/deploy-if-changed.sh user@server

# Check deployment status
./deploy/linux-server/get-status.sh user@server

# Remove deployment completely
./deploy/linux-server/deploy-purge.sh user@server
```

---

## CI/CD Pipeline

The generated `.github/workflows/build.yml` provides:

1. **Build** - Creates Docker image on tag push
2. **Push** - Pushes to GitHub Container Registry
3. **Deploy** - Optionally triggers deployment

### Triggering Builds

Builds are triggered by version tags:

```bash
git tag v1.0.0
git push origin v1.0.0
```

### GitHub Secrets

Configure these secrets in your repository:

| Secret        | Description           |
| ------------- | --------------------- |
| `DEPLOY_HOST` | Server hostname or IP |
| `DEPLOY_USER` | SSH username          |
| `DEPLOY_KEY`  | SSH private key       |

---

## Scaling

The production Dockerfile runs uvicorn with multiple workers:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--workers", "4"]
```

Adjust workers based on CPU cores (2 \* cores + 1 is a common formula).

For horizontal scaling, run multiple container instances behind a load balancer.

---

## Platform-Specific Examples

### Fly.io

```bash
# Create app
fly launch --no-deploy

# Create and attach Postgres
fly postgres create
fly postgres attach

# Run migrations
fly ssh console -C "paxx db upgrade"

# Deploy
fly deploy
```

### Railway

1. Create project with Postgres addon
2. `DATABASE_URL` is automatically set from the addon
3. Deploy via GitHub or `railway up`
4. Run migrations: `railway run paxx db upgrade`

### AWS ECS

1. Push image to ECR
2. Create task definition with environment variables
3. Run migration as one-off task before deploying
4. Update service with new task definition

### Generic Docker Host

```bash
# Build and push
docker build -t myregistry/myapp:latest .
docker push myregistry/myapp:latest

# On server
docker pull myregistry/myapp:latest
docker run -d \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="..." \
  -p 8000:8000 \
  myregistry/myapp:latest
```

---

## Monitoring

### Logs

View application logs:

```bash
# Local development
docker compose logs -f app

# Production (linux-server)
ssh user@server
cd /opt/myapp
docker compose logs -f app
```

### Health Status

```bash
curl https://your-domain.com/health
```

### Metrics

Add the metrics infrastructure component for Prometheus and OpenTelemetry:

```bash
paxx infra add metrics
```

See [Infrastructure](infrastructure.md) for details.

## Next Steps

Read the [CLI Reference](cli-reference.md) for all available commands
