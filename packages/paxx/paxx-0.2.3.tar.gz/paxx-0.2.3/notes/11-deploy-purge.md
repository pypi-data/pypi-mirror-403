# Deploy Purge Script Plan

Complete cleanup script to remove all deployment artifacts from a server.

## Design Decisions

- **Full purge only** - removes everything including database (no soft/partial modes)
- **Runs on server directly** (like `server-setup.sh`) - destructive operations should require explicit server access, not remote execution

## Resources to Remove

| Category | Resource | Created By |
|----------|----------|------------|
| **Docker Containers** | `traefik`, `db` (postgres), `{app}-blue`, `{app}-green` | docker-compose.yml, deploy.sh |
| **Docker Networks** | `traefik-public`, `backend` | server-setup.sh |
| **Docker Volumes** | `postgres_data` | docker-compose.yml |
| **Docker Images** | traefik, postgres, app images | pulled during deploy |
| **Directories** | `/opt/{project_name}`, `/var/log/{project_name}` | server-setup.sh |
| **Cron Job** | `/etc/cron.d/{project_name}-deploy` | server-setup.sh |
| **Lock File** | `/tmp/{project_name}-deploy.lock` | deploy-if-changed.sh |
| **Firewall Rules** | ufw allow 80/tcp, 443/tcp | server-setup.sh |
| **Docker Group** | user added to docker group | server-setup.sh |
| **Docker Service** | systemctl enable docker | server-setup.sh |
| **Docker** | Docker engine itself | server-setup.sh |
| **Packages** | jq (and potentially others) | server-setup.sh |

## Script Structure

```
1. RECONNAISSANCE
   - Detect what exists on the system
   - Categorize findings

2. REPORT
   - Show findings grouped by severity:
     - DESTRUCTIVE (data loss): postgres volume, app data
     - SAFE: containers, networks, cron, lock files
     - OPTIONAL: firewall rules, docker group membership

3. CONFIRMATION
   - Show exact commands that will run
   - Require explicit "PURGE" confirmation (not just y/n)

4. EXECUTION
   - Proper order: containers → compose down → networks → volumes → filesystem
   - Log each action
   - Report success/failure
```

---

## Update Plan (v2)

### Issues Found in Testing

1. **Dynamic warning message** - Warning says "This will permanently delete all data including the PostgreSQL database!" even when no volumes are found. Should be context-aware.

2. **Firewall rules** - Listed as "OPTIONAL" but should just be included in the purge. No options, just purge everything.

3. **Missing reconnaissance for infrastructure images** - Only detects app images, not traefik:latest or postgres:16-alpine.

4. **Missing items from server-setup.sh**:
   - Docker group membership (user removed from docker group)
   - Docker service (systemctl disable docker)
   - Docker engine removal
   - Package removal (jq installed by server-setup.sh)

### Design Decision

**No options - just confirm and purge everything.** If user confirms with PURGE, remove all deployment artifacts including:
- All containers, networks, volumes, images
- All directories and files
- Firewall rules (80/tcp, 443/tcp)
- Docker group membership
- Docker service
- Docker itself
- Packages (jq)

### Updated Script Flow

```
1. RECONNAISSANCE
   - Detect containers (traefik, db, app-blue, app-green)
   - Detect networks (traefik-public, backend)
   - Detect volumes (postgres_data, {project}_postgres_data)
   - Detect images (app images + traefik + postgres)
   - Detect directories (/opt/{project}, /var/log/{project})
   - Detect files (cron job, lock file)
   - Detect firewall rules (80/tcp, 443/tcp)
   - Detect system changes (docker group, docker installed, jq installed)

2. REPORT
   - DESTRUCTIVE: volumes (if any)
   - DEPLOYMENT: containers, networks, images, directories, files, firewall
   - SYSTEM: docker, docker group, packages

3. SHOW ACTIONS
   - List ALL commands that will run

4. CONFIRMATION
   - Dynamic warning based on what's found
   - Require "PURGE" to confirm

5. EXECUTION (in order)
   - Containers stop/rm
   - Docker compose down
   - Networks rm
   - Volumes rm
   - Images rm
   - Directories rm
   - Files rm
   - Firewall rules delete
   - Docker group membership remove
   - Docker service disable
   - Docker uninstall
   - Packages remove (jq)
```

### Implementation Checklist

- [x] Add infrastructure image detection (traefik, postgres)
- [x] Add firewall rules to main purge (not optional)
- [x] Make warning message dynamic based on volumes found
- [x] Add docker group removal: `gpasswd -d $SUDO_USER docker`
- [x] Add docker service disable: `systemctl disable docker && systemctl stop docker`
- [x] Add docker removal: `apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin`
- [x] Add docker cleanup: `rm -rf /var/lib/docker /var/lib/containerd`
- [x] Add jq removal: `apt-get purge -y jq`
- [x] Add apt autoremove: `apt-get autoremove -y`
- [x] Restructure report: DESTRUCTIVE / DEPLOYMENT / SYSTEM categories
- [x] Remove all optional questions - just PURGE confirmation
