# Paxx Deployment to Linux Server

## Overview

Deploy paxx-generated apps to any Linux server (Debian, Ubuntu, Raspbian, etc.) with zero-downtime deployments.

## Proposed Flow

1. Bootstrap a paxx app
2. Add example feature(s)
3. Create a Docker image (matching target architecture)
4. Push to registry (or transfer directly)
5. Server pulls and deploys with blue-green strategy
6. Traefik handles traffic switching based on health checks
7. Old container gracefully drains and shuts down

## Flow Analysis

| Step | Proposal | Industry Standard | Verdict |
|------|----------|-------------------|---------|
| Bootstrap + features | Works | Same | OK |
| Build Docker image | "where/how?" | CI/CD or local to registry | Need to decide |
| Transfer to server | Direct transfer | Pull from registry | Registry is better |
| Deploy with traffic switch | nginx | Traefik (auto-discovery) | Traefik simpler |
| Health-based cutover | Good idea | Same + graceful drain | OK |
| Env prep script | Good idea | Same | OK |

## Key Decisions & Recommendations

### 1. Where to Build Docker Images

**Option A: Build locally (cross-compile if needed)** — Recommended for simplicity
```bash
# For ARM64 targets (Raspberry Pi, AWS Graviton, etc.)
docker buildx build --platform linux/arm64 -t myapp:latest .

# For x86_64 targets (most VPS, cloud VMs)
docker buildx build --platform linux/amd64 -t myapp:latest .
```

**Option B: Build on target server** — Slower but native
- Works but low-powered servers (like Raspberry Pi) build slowly

**Option C: GitHub Actions** — Best for teams/automation
- Build on push, push to registry, server pulls

**Decision:** Use **GitHub Actions** to build on git tags. This mirrors industry standard CI/CD practice — tag a release, image gets built automatically, then deploy when ready.

#### Build Trigger Strategy

| Trigger | Use Case |
|---------|----------|
| Every commit to main | Fast iteration, always-deployable |
| **On tags only (v1.0.0)** | More controlled, explicit releases ✓ |
| Manual trigger | Full control, deploy when ready |

#### GitHub Actions Workflow

Add this to your app repo at `.github/workflows/build.yml`:

```yaml
name: Build and Push

on:
  push:
    tags:
      - 'v*'  # Triggers on v1.0.0, v2.1.3, etc.

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write  # Needed for GHCR

    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.ref_name }}
            ghcr.io/${{ github.repository }}:latest
```

#### Release Flow

```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions automatically builds and pushes to GHCR

# On server, pull the image
docker pull ghcr.io/yourusername/yourapp:v1.0.0
```

### 2. Image Transfer: Registry vs Direct

| Method | Pros | Cons |
|--------|------|------|
| **Registry (GHCR/Docker Hub)** | Standard, versioned, rollback easy, works from anywhere | Needs internet, account setup |
| **Direct transfer (docker save/load)** | Simple, no accounts | Manual, no versioning, local network only |

**Decision:** Use **GitHub Container Registry (GHCR)** — free unlimited storage/transfer for public repos, easy auth (uses existing GitHub token), industry standard. Images live alongside your repo code.

### 3. Load Balancer: Nginx vs Traefik

For this use case, **Traefik** is better because:
- Auto-discovers Docker containers via labels
- Built-in health checks
- Automatic Let's Encrypt SSL
- No config file editing on each deploy

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Dev Machine                            │
│        paxx bootstrap → add features → git tag → push       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (git push tag)
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│              docker build → push to GHCR                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (image pushed)
                    ┌─────────────────┐
                    │  GitHub GHCR    │
                    │  myapp:v1.0.0   │
                    └─────────────────┘
                              │
                              ▼ (pull)
┌─────────────────────────────────────────────────────────────┐
│                       Linux Server                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                      Traefik                           │ │
│  │              (port 80/443, health checks)              │ │
│  └───────────┬───────────────────────┬────────────────────┘ │
│              │                       │                      │
│              ▼                       ▼                      │
│  ┌───────────────────┐   ┌───────────────────┐             │
│  │   app-blue:v1.0   │   │  app-green:v1.1   │             │
│  │   (old, draining) │   │  (new, active)    │             │
│  └───────────────────┘   └───────────────────┘             │
│              │                       │                      │
│              └───────────┬───────────┘                      │
│                          ▼                                  │
│              ┌───────────────────┐                          │
│              │    PostgreSQL     │                          │
│              │   (persistent)    │                          │
│              └───────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Files to Add to Paxx

New deployment-related files for generated projects:

```
{project}/
├── deploy/
│   ├── build.yml.example        # GitHub Actions workflow (copy to .github/workflows/) ✓
│   ├── docker-compose.local.yml # Local network: direct IP access, no SSL ✓
│   ├── .env.local.example       # Local network env template ✓
│   ├── docker-compose.prod.yml  # Public: Traefik + Let's Encrypt SSL ✓
│   ├── .env.prod.example        # Public env template (domain, ACME email) ✓
│   ├── server-setup.sh          # One-time server environment prep (TODO)
│   └── deploy.sh                # Blue-green deploy script (TODO)
```

### Deployment Options

| Use Case | Compose File | Access |
|----------|--------------|--------|
| Local network (home lab, Raspberry Pi) | `docker-compose.local.yml` | `http://<server-ip>` |
| Public server with domain | `docker-compose.prod.yml` | `https://yourdomain.com` |

### 1. server-setup.sh

Idempotent setup script (works on Debian, Ubuntu, Raspbian):
- Detect distro and architecture
- Install Docker + docker-compose
- Configure Docker for non-root
- Set up firewall (ufw)
- Create app directories
- Set up Docker network for Traefik

```bash
# Distro detection (for Docker repo setup)
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID  # debian, ubuntu, raspbian
fi

# Architecture detection (for image pulls)
ARCH=$(uname -m)  # aarch64, x86_64
```

### 2. deploy.sh

Zero-downtime deploy script:
- Pull new image
- Start new container (green)
- Wait for health check
- Update Traefik routing
- Graceful drain of old container (blue)
- Remove old container

### 3. docker-compose.prod.yml

Production stack:
- Traefik with auto-SSL
- App with health checks and Traefik labels
- PostgreSQL with persistent volume
- Proper restart policies

## Distro Compatibility

| Feature | Debian | Ubuntu | Raspbian |
|---------|--------|--------|----------|
| Package manager | apt | apt | apt |
| Init system | systemd | systemd | systemd |
| Firewall | ufw | ufw | ufw |
| Docker install | get.docker.com | get.docker.com | get.docker.com |

The only variable is **architecture**:
- Raspberry Pi, AWS Graviton, Apple Silicon VMs → ARM64 (`linux/arm64`)
- Most VPS, cloud VMs, x86 servers → x86_64 (`linux/amd64`)

## Open Questions

1. **Database location**: Should Postgres run on the server too, or separate DB server?

2. **Domain/SSL**: HTTPS with real domain (e.g., `myapp.home.local` with self-signed, or `myapp.yourdomain.com` with Let's Encrypt)?

3. ~~**Registry preference**: GHCR (free, GitHub auth), Docker Hub (simpler), or direct transfer (no internet needed)?~~ **Decided: GHCR with GitHub Actions build on tags**

4. **Single app or multiple**: Will server host just one app or potentially multiple paxx apps?

5. ~~**Auto-deploy trigger**: How does server know when new image is available?~~ **Decided: Cron-based polling**

## Current Paxx Docker Support

Already exists in templates:

- `Dockerfile.jinja` — Multi-stage production build, 4 uvicorn workers, python:3.12-slim
- `Dockerfile.dev.jinja` — Development with hot-reload
- `docker-compose.yml.jinja` — Dev stack with app + PostgreSQL 16 Alpine
- `.dockerignore.jinja` — 59+ exclusion patterns
- `DEPLOY.md.jinja` — Basic deployment guide
- `/health` endpoint — Returns 200/503 based on DB connectivity

## Comparison to Hosting Platforms

What Fly.io/Render/Railway do:

1. **Build**: Happens on CI/CD or platform (not local)
2. **Registry**: Images pushed to container registry
3. **Deploy**: Target pulls from registry (not push-based)
4. **Health checks**: New container verified healthy before traffic switch
5. **Graceful shutdown**: Old container gets time to finish in-flight requests
6. **Rollback**: Easy revert to previous version via image tags

Our server setup should mirror this pattern as closely as possible.

## Next Steps

1. Decide on open questions above
2. Implement deploy/ scripts as paxx templates
3. Add `paxx deploy` CLI command (optional)
4. Test full flow on actual server
5. Document in main README

---

# Implementation Plan: Local Network Blue-Green Deployment

## Scope

Focus on **local network deployment only** (access via IP, no domain/SSL). Public deployment can be added later.

## Blue-Green Flow

```
1. New image available
2. Start NEW container (green) alongside OLD (blue)
3. Wait for green health check to pass
4. Switch load balancer to green     ← ZERO DOWNTIME
5. Drain old container (finish in-flight requests)
6. Stop and remove old container
```

**Key requirement**: Load balancer to switch traffic without downtime.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Linux Server                          │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Traefik                             │ │
│  │              (port 80, no SSL)                         │ │
│  │         Routes to healthy app container                │ │
│  └───────────────────────┬────────────────────────────────┘ │
│                          │                                  │
│            ┌─────────────┴─────────────┐                   │
│            │                           │                    │
│            ▼                           ▼                    │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │   app (blue)     │      │   app (green)    │            │
│  │   :8000          │      │   :8000          │            │
│  │   priority=1     │      │   priority=2     │            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                         │                       │
│           └────────────┬────────────┘                       │
│                        ▼                                    │
│              ┌──────────────────┐                           │
│              │   PostgreSQL     │                           │
│              │   :5432          │                           │
│              └──────────────────┘                           │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   deploy.sh                            │ │
│  │  - Polls GHCR for new images (every 5 min via cron)    │ │
│  │  - Orchestrates blue-green switch                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Components

**Load balancer**: Traefik (auto-discovers containers via Docker labels, no config changes needed on deploy)

### 1. Traefik (load balancer)

Minimal config for local network:
```yaml
traefik:
  image: traefik:v3.0
  command:
    - "--providers.docker=true"
    - "--providers.docker.exposedbydefault=false"
    - "--entrypoints.web.address=:80"
    # No SSL config needed for local
  ports:
    - "80:80"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
```

### 2. App Container Labels

```yaml
app:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.app.rule=PathPrefix(`/`)"
    - "traefik.http.routers.app.entrypoints=web"
    - "traefik.http.services.app.loadbalancer.server.port=8000"
    # Health check - Traefik won't route until healthy
    - "traefik.http.services.app.loadbalancer.healthcheck.path=/health"
    - "traefik.http.services.app.loadbalancer.healthcheck.interval=5s"
```

### 3. deploy.sh (blue-green orchestrator)

```bash
#!/bin/bash
# Usage: ./deploy.sh [version]
# If no version specified, uses :latest

VERSION=${1:-latest}
IMAGE="ghcr.io/${GITHUB_REPOSITORY}:${VERSION}"

# 1. Pull new image
docker pull $IMAGE

# 2. Determine current slot (blue or green)
CURRENT=$(docker ps --filter "name=app-" --format "{{.Names}}" | head -1)
if [[ $CURRENT == *"blue"* ]]; then
    NEW_SLOT="green"
    OLD_SLOT="blue"
else
    NEW_SLOT="blue"
    OLD_SLOT="green"
fi

# 3. Start new container
docker compose -f docker-compose.yml run -d --name app-$NEW_SLOT app

# 4. Wait for health check
echo "Waiting for app-$NEW_SLOT to be healthy..."
until curl -sf http://localhost:8001/health; do  # New container on different port
    sleep 2
done

# 5. Traefik automatically routes to healthy container
# Old container can be stopped now

# 6. Graceful shutdown of old container
docker stop --time 30 app-$OLD_SLOT
docker rm app-$OLD_SLOT

echo "Deployed $VERSION to app-$NEW_SLOT"
```

### 4. Auto-polling

Cron job that checks for new images:
```bash
# /etc/cron.d/app-deploy
*/5 * * * * root /opt/app/deploy-if-changed.sh >> /var/log/app-deploy.log 2>&1
```

```bash
#!/bin/bash
# deploy-if-changed.sh - Check for new image and deploy if found

IMAGE="ghcr.io/${GITHUB_REPOSITORY}:latest"

# Get local image digest
LOCAL_DIGEST=$(docker images --digests --format "{{.Digest}}" $IMAGE)

# Get remote digest (without pulling)
REMOTE_DIGEST=$(docker manifest inspect $IMAGE 2>/dev/null | jq -r '.manifests[0].digest // .config.digest')

if [[ "$LOCAL_DIGEST" != "$REMOTE_DIGEST" ]]; then
    echo "$(date): New image detected, deploying..."
    /opt/app/deploy.sh latest
else
    echo "$(date): No new image"
fi
```

## Files to Create

```
deploy/
├── docker-compose.yml       # Traefik + app + db
├── .env.example             # GITHUB_REPOSITORY, POSTGRES_PASSWORD
├── deploy.sh                # Blue-green deploy script
├── deploy-if-changed.sh     # Polling script for cron
├── server-setup.sh          # One-time server setup
└── build.yml.example        # GitHub Actions (already exists)
```

## Deployment Flow (User Perspective)

### First-time setup
```bash
# On server
scp -r deploy/ user@server:~/myapp/
ssh user@server
cd myapp
./server-setup.sh              # Install Docker, setup cron
cp .env.example .env           # Configure
docker compose up -d           # Start Traefik + DB + initial app
```

### Normal release flow
```bash
# On dev machine
git tag v1.2.0
git push origin v1.2.0
# GitHub Actions builds and pushes to GHCR
# Server's cron job detects new image within 5 minutes
# Blue-green deploy happens automatically
```

### Manual deploy (if needed)
```bash
ssh user@server
cd myapp
./deploy.sh v1.2.0   # Deploy specific version
```

## Rollback

```bash
./deploy.sh v1.1.0   # Just deploy the old version
```

Since we tag versions in GHCR, any previous version can be deployed instantly.

## Implementation Order

1. **docker-compose.yml** - Traefik + app + PostgreSQL
2. **deploy.sh** - Blue-green orchestration logic
3. **.env.example** - Environment template
4. **deploy-if-changed.sh** - Polling script
5. **server-setup.sh** - One-time setup (Docker, cron, directories)
6. **Test full flow** on actual server
7. **Clean up** - Remove old files (docker-compose.local.yml, docker-compose.prod.yml)

---

## Current State (Jan 2026)

### What exists in `deploy-examples/linux-server/`:

| File | Status |
|------|--------|
| `build.yml.example.jinja` | Done - GitHub Actions workflow |
| `server-setup.sh.jinja` | Partial - installs Docker, firewall, dirs, BUT **no cron job** |
| `deploy-init.sh.jinja` | Partial - copies files to server |
| `use-deployment.sh.jinja` | Partial - installs deployment locally |

### What's missing:

| File | Purpose |
|------|---------|
| `docker-compose.yml.jinja` | **Main orchestration** - Traefik + app (blue/green) + PostgreSQL |
| `deploy.sh.jinja` | **Blue-green deploy script** - pull image, start new container, health check, stop old |
| `deploy-if-changed.sh.jinja` | **Polling script** - checks GHCR for new image, calls deploy.sh if changed |
| `.env.example.jinja` | **Environment template** - IMAGE, POSTGRES_PASSWORD, etc. (currently inline in use-deployment.sh) |

### Implementation Tasks

1. [DONE] **Create `docker-compose.yml.jinja`**
   - Traefik service (port 80, Docker provider)
   - App service with Traefik labels (health check, routing)
   - PostgreSQL with persistent volume
   - Uses `traefik-public` network

2. [DONE] **Create `deploy.sh.jinja`**
   - Determines current slot (blue/green)
   - Pulls new image
   - Starts new container
   - Waits for health check
   - Stops/removes old container

3. [DONE] **Create `deploy-if-changed.sh.jinja`**
   - Compares local vs remote image digest
   - Calls `deploy.sh` if different

4. [DONE] **Create `.env.example.jinja`**
   - `IMAGE=ghcr.io/YOUR_USERNAME/{{ project_name }}:latest`
   - `POSTGRES_PASSWORD=...`
   - `GITHUB_REPOSITORY=...`

5. [DONE] **Update `server-setup.sh.jinja`**
   - Add cron job setup: `*/5 * * * * /opt/{{ project_name }}/deploy-if-changed.sh`

6. [DONE] **Update `use-deployment.sh.jinja`**
   - Copy the new files (docker-compose.yml, deploy.sh, deploy-if-changed.sh, .env.example)

7. [DONE] **Update `deploy-init.sh.jinja`**
   - Copy all necessary files to server

### Dependency Order

```
1. docker-compose.yml.jinja  (no deps)
2. deploy.sh.jinja           (uses docker-compose.yml)
3. deploy-if-changed.sh.jinja (calls deploy.sh)
4. .env.example.jinja        (no deps)
5. Update server-setup.sh    (references deploy-if-changed.sh path)
6. Update use-deployment.sh  (copies all files)
7. Update deploy-init.sh     (copies all files to server)
```
