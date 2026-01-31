# Extensions

Extensions are add-ons that enhance existing infrastructure.

## Overview

```bash
# List available extensions
paxx ext list

# Add an extension
paxx ext add <name>
```

When you add an extension, paxx:

1. Renders templates to `services/`
2. Adds dependencies to `pyproject.toml`
3. Adds environment variables to `settings.py` and `.env.example`

---

## ARQ (Background Tasks)

Background task queue using ARQ (async Redis queue).

```bash
paxx ext add arq
```

### Prerequisites

Redis must be configured. Run `paxx infra add redis` first.

### Generated Files

- `services/arq.py` - ARQ client and task enqueueing
- `v/tasks.py` - Worker settings and task definitions

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARQ_REDIS_URL` | `redis://localhost:6379/1` | Redis URL for task queue |
| `ARQ_MAX_JOBS` | `10` | Maximum concurrent jobs |
| `ARQ_JOB_TIMEOUT` | `300` | Job timeout in seconds |

### Usage

Define tasks in `services/tasks.py`:

```python
async def send_welcome_email(ctx, user_id: int):
    """Send welcome email to a new user."""
    print(f"Sending welcome email to user {user_id}")

class WorkerSettings:
    functions = [send_welcome_email]
    redis_settings = RedisSettings.from_dsn(settings.arq_redis_url)
```

Enqueue tasks from your code:

```python
from services.arq import enqueue

# Enqueue a task
await enqueue("send_welcome_email", user_id=123)

# With delay
await enqueue("send_reminder", user_id=123, _defer_by=timedelta(hours=24))
```

### Running the Worker

```bash
uv run arq services.tasks.WorkerSettings
```

### Dependency

- `arq>=0.26`

---

## WebSocket

WebSocket connection manager with room support and optional Redis pub/sub for multi-instance scaling.

```bash
paxx ext add websocket
```

### Generated Files

- `services/ws.py` - WebSocket manager with room support

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WS_REDIS_URL` | - | Redis URL for multi-instance pub/sub |
| `WS_HEARTBEAT_INTERVAL` | `30` | Heartbeat interval in seconds |

### Usage

Basic WebSocket endpoint:

```python
from fastapi import WebSocket, WebSocketDisconnect
from services.ws import manager

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
```

Room support:

```python
# Join a room
await manager.join_room(client_id, "chat-room")

# Send to room
await manager.broadcast_to_room("chat-room", {"message": "Hello!"})

# Leave room
await manager.leave_room(client_id, "chat-room")
```

### Multi-Instance Mode

For running multiple app instances behind a load balancer:

1. Set `WS_REDIS_URL` environment variable
2. Start pub/sub in your app lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.start_pubsub()
    yield
    await manager.stop_pubsub()
```

### Dependencies

No additional dependencies (uses existing FastAPI WebSocket support).

---

## PostGIS

PostGIS geospatial extension for PostgreSQL, enabling location-based queries.

```bash
paxx ext add postgis
```

### What It Does

- Upgrades your PostgreSQL image to `postgis/postgis`
- Adds GeoAlchemy2 for SQLAlchemy integration
- Provides helper functions for common geospatial queries

### Generated Files

- `services/geo.py` - Geography types and query helpers

### Usage

Define location fields in models:

```python
from services.geo import Geography
from sqlalchemy.orm import Mapped, mapped_column

class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        index=True,  # Creates GIST index
    )
```

Query helpers:

```python
from services.geo import distance_within, bbox_filter, distance_meters

# Find locations within 100 meters of a point
stmt = select(Location).where(
    distance_within(Location.location, lat=52.52, lng=13.4, radius_meters=100)
)

# Viewport/bounding box query
stmt = select(Location).where(
    bbox_filter(Location.location, west=13.0, south=52.0, east=14.0, north=53.0)
)

# Calculate distance between points
stmt = select(
    Location,
    distance_meters(Location.location, lat=52.52, lng=13.4).label("distance")
).order_by("distance")
```

### Important

After adding PostGIS, restart your database:

```bash
docker compose down && docker compose up -d
```

### Dependencies

- `geoalchemy2>=0.14`

---

## Summary

| Extension | Purpose | Requires | Key Files |
|-----------|---------|----------|-----------|
| **arq** | Background tasks | redis | `services/arq.py`, `services/tasks.py` |
| **websocket** | Real-time connections | (optional redis) | `services/ws.py` |
| **postgis** | Geospatial queries | - | `services/geo.py` |

## Best Practices

1. **Check prerequisites** - Some extensions require infrastructure components (e.g., ARQ requires Redis)
2. **Development vs Production** - Configure production services separately from local development
3. **Environment variables** - Always configure production values via environment variables
4. **Dependencies** - Run `uv sync` after adding extensions to install new dependencies

## Next Steps

Set up [Deployment](deployment.md) for production
