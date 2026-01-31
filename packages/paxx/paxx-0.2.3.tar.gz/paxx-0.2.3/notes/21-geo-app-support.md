# Geo-App Architecture Support Analysis

## Context

Analysis of whether the architecture described in `../geo-app/docs/1-architecture/FROM_GPT5.md` (Geo-based Code Hunt Game) can be implemented using a paxx-bootstrapped application.

## Architecture Requirements (from FROM_GPT5.md)

The geo-app requires:
- FastAPI REST backend with WebSocket support
- PostgreSQL with PostGIS for geospatial queries
- Redis for caching (viewport tiles) and pub/sub
- Background workers for notifications, fanout, media processing
- S3-compatible storage for media with presigned URLs
- Real-time messaging with room support
- Domain-driven features (users, items, hides, claims, messaging, activities)

## Paxx Coverage

### Fully Supported Out of Box

| Requirement | Paxx Module | Notes |
|-------------|-------------|-------|
| FastAPI REST backend | Core scaffold | App factory, async routes |
| SQLAlchemy async models | Core scaffold | Pydantic v2 schemas |
| Alembic migrations | Core scaffold | Auto-configured |
| Domain-driven features | `paxx feature create` | models, schemas, services, routes |
| Redis caching | `paxx infra add redis` | Async client, get/set/delete with TTL |
| Background workers | `paxx infra add arq` | Enqueue, defer, job status |
| S3 storage + presigned URLs | `paxx infra add storage` | Pluggable backend (local dev, S3 prod) |
| WebSocket messaging | `paxx infra add websocket` | Rooms, broadcast, Redis pub/sub for scaling |
| Metrics/tracing | `paxx infra add metrics` | OpenTelemetry support |
| PostGIS geospatial | `paxx infra add postgis` | Geography types, spatial query helpers |

### Feature Mapping

The geo-app domain concepts map directly to paxx features:

```bash
paxx feature create users      # profiles, follows, friendships
paxx feature create items      # item codes, ownership
paxx feature create hides      # geolocation, visibility
paxx feature create claims     # proximity verification
paxx feature create messaging  # chats, messages
paxx feature create activities # feed
paxx feature create currencies # balances, transactions
paxx feature create media      # S3 references
```

### Infrastructure Setup

```bash
paxx bootstrap geo-app
cd geo-app

# Add all required infrastructure
paxx infra add redis
paxx infra add postgis
paxx infra add arq
paxx infra add storage
paxx infra add websocket

uv sync
docker compose up -d
```

## Key Geo-App Patterns Supported

### 1. Viewport Queries (Map Loading)

Using `core/geo.py` from postgis infra:

```python
from core.geo import bbox_filter

async def get_hides_in_viewport(db, west, south, east, north):
    stmt = select(Hide).where(
        Hide.active == True,
        bbox_filter(Hide.location, west, south, east, north)
    ).limit(100)
    return (await db.execute(stmt)).scalars().all()
```

### 2. Proximity Verification (Claims)

```python
from core.geo import distance_within

async def verify_claim_proximity(db, hide_id, lat, lng, max_distance=100):
    stmt = select(Hide).where(
        Hide.id == hide_id,
        Hide.active == True,
        distance_within(Hide.location, lat, lng, max_distance)
    )
    return (await db.execute(stmt)).scalar_one_or_none()
```

### 3. Real-time Messaging

Using `core/ws.py` from websocket infra:

```python
from core.ws import manager

@app.websocket("/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            chat_id = data["chat_id"]
            await manager.broadcast_to_room(f"chat:{chat_id}", data)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
```

### 4. Background Notifications

Using `core/arq.py` and `core/tasks.py` from arq infra:

```python
# In core/tasks.py
async def notify_nearby_users(ctx, hide_id: str, lat: float, lng: float):
    """Notify users within radius of new hide."""
    # Query users with last_known_location within radius
    # Send push notifications via FCM/APNs
    pass

# In services
from core.arq import enqueue
await enqueue("notify_nearby_users", hide_id=hide.id, lat=lat, lng=lng)
```

### 5. Media Upload with Presigned URLs

Using `core/storage.py` from storage infra:

```python
from core.storage import get_storage

@router.post("/media/sign")
async def get_upload_url(filename: str):
    storage = get_storage()
    key = f"uploads/{uuid4()}/{filename}"
    url = await storage.presign(key, expires_in=3600)
    return {"upload_url": url, "key": key}
```

## Verdict

**The geo-app architecture is fully implementable on paxx.**

All major components are covered:
- Core stack (FastAPI, SQLAlchemy async, Pydantic v2, Alembic)
- Infrastructure (Redis, PostGIS, ARQ workers, S3, WebSocket)
- Domain-driven feature organization

No architectural changes or workarounds needed. The paxx-generated project provides the right foundation, and all geo-specific functionality (spatial queries, real-time messaging, background jobs) is available through the infra modules.

## Additional Considerations

### Auth (Cognito/Auth0)
Not included in paxx but easily added:
- Add `python-jose` or `authlib` dependency
- Create JWT validation middleware in `core/dependencies.py`
- Configure JWKS endpoint in settings

### Push Notifications (FCM/APNs)
Would need custom implementation:
- Add `firebase-admin` or similar
- Create notification service in a feature or core module
- Integrate with ARQ workers for async delivery

### Rate Limiting
Could add as future paxx infra module or use:
- `slowapi` for simple rate limiting
- Redis-based custom implementation for distributed limits
