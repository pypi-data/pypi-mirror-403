# WebSockets Implementation Plan

Real-time WebSocket support for notifications, chat, live dashboards, and broadcasting in Paxx-generated projects.

---

## Overview

WebSockets enable real-time bidirectional communication between clients and server. The implementation provides:

- **ConnectionManager class** - manage client connections, rooms, and broadcasting
- **Room/channel support** - group connections for targeted messaging
- **Redis pub/sub integration** - multi-instance support for horizontal scaling
- **Native FastAPI WebSocket support** - no additional frameworks needed

---

## Implementation Structure

```
src/paxx/infra/websocket/
├── __init__.py
├── config.py
├── dependencies.txt
├── docker_service.yml          # Empty - reuses Redis
└── templates/
    └── ws.py.jinja             # ConnectionManager + utilities
```

---

## 1. Config (`config.py`)

```python
"""WebSocket infrastructure configuration."""

from dataclasses import dataclass, field


@dataclass
class InfraConfig:
    """Configuration for WebSocket infrastructure."""

    name: str = "websocket"
    docker_service: str = ""  # Reuses existing Redis service for pub/sub
    core_files: list[str] = field(default_factory=lambda: ["ws.py"])
    dependencies: list[str] = field(default_factory=list)  # No extra deps needed
    env_vars: dict[str, str] = field(
        default_factory=lambda: {
            "WS_REDIS_URL": "",
            "WS_HEARTBEAT_INTERVAL": "30",
        }
    )
```

**Notes:**
- `WS_REDIS_URL` is optional - only needed for multi-instance deployments
- If empty, falls back to in-memory connection management (single instance only)
- `WS_HEARTBEAT_INTERVAL` is the ping interval in seconds to keep connections alive

---

## 2. Dependencies (`dependencies.txt`)

```
# No additional dependencies required
# FastAPI has native WebSocket support
# redis-py is already included if Redis infra is added
```

Empty file - FastAPI includes WebSocket support by default. Redis pub/sub uses the existing Redis dependency if needed.

---

## 3. Docker Service (`docker_service.yml`)

Empty file - WebSockets reuse the Redis service for pub/sub. The `infra.py` already handles missing docker services gracefully.

If Redis hasn't been added and multi-instance support is needed, users will need to add it first.

---

## 4. WebSocket Template (`templates/ws.py.jinja`)

```python
"""
WebSocket connection manager with room support.

Supports single-instance (in-memory) and multi-instance (Redis pub/sub) deployments.

Usage:
    from core.ws import manager

    # In your WebSocket route:
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await manager.connect(websocket, client_id)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(f"Client {client_id}: {data}")
        except WebSocketDisconnect:
            manager.disconnect(client_id)

    # Join/leave rooms:
    await manager.join_room(client_id, "chat-room-1")
    await manager.broadcast_to_room("chat-room-1", {"type": "message", "text": "Hello!"})
    await manager.leave_room(client_id, "chat-room-1")

    # Send to specific client:
    await manager.send_personal(client_id, {"type": "notification", "text": "Welcome!"})
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a WebSocket connection."""

    websocket: WebSocket
    client_id: str
    rooms: set[str] = field(default_factory=set)


class ConnectionManager:
    """
    Manages WebSocket connections with room support.

    For single-instance deployments, uses in-memory connection tracking.
    For multi-instance deployments, uses Redis pub/sub for cross-instance messaging.
    """

    def __init__(self):
        self._connections: dict[str, Connection] = {}
        self._rooms: dict[str, set[str]] = {}  # room_name -> set of client_ids
        self._redis_pubsub = None
        self._pubsub_task = None

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        accept: bool = True,
    ) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            client_id: Unique identifier for this client
            accept: Whether to accept the connection (set False if already accepted)
        """
        if accept:
            await websocket.accept()

        self._connections[client_id] = Connection(
            websocket=websocket,
            client_id=client_id,
        )
        logger.debug(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str) -> None:
        """
        Remove a client from all rooms and unregister the connection.

        Args:
            client_id: The client to disconnect
        """
        if client_id not in self._connections:
            return

        connection = self._connections[client_id]

        # Remove from all rooms
        for room in list(connection.rooms):
            self._leave_room_internal(client_id, room)

        del self._connections[client_id]
        logger.debug(f"WebSocket disconnected: {client_id}")

    async def send_personal(self, client_id: str, message: dict | str) -> bool:
        """
        Send a message to a specific client.

        Args:
            client_id: Target client ID
            message: Message to send (dict will be JSON encoded)

        Returns:
            True if sent successfully, False if client not found
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False

        try:
            if isinstance(message, dict):
                await connection.websocket.send_json(message)
            else:
                await connection.websocket.send_text(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to {client_id}: {e}")
            self.disconnect(client_id)
            return False

    async def broadcast(self, message: dict | str, exclude: set[str] | None = None) -> int:
        """
        Send a message to all connected clients.

        Args:
            message: Message to send
            exclude: Set of client_ids to exclude from broadcast

        Returns:
            Number of clients the message was sent to
        """
        exclude = exclude or set()
        sent_count = 0

        # Local broadcast
        for client_id in list(self._connections.keys()):
            if client_id not in exclude:
                if await self.send_personal(client_id, message):
                    sent_count += 1

        # Cross-instance broadcast via Redis
        if settings.ws_redis_url:
            await self._publish("__broadcast__", message, exclude)

        return sent_count

    async def join_room(self, client_id: str, room: str) -> bool:
        """
        Add a client to a room.

        Args:
            client_id: Client to add
            room: Room name to join

        Returns:
            True if joined successfully
        """
        connection = self._connections.get(client_id)
        if not connection:
            return False

        if room not in self._rooms:
            self._rooms[room] = set()

        self._rooms[room].add(client_id)
        connection.rooms.add(room)

        logger.debug(f"Client {client_id} joined room: {room}")
        return True

    async def leave_room(self, client_id: str, room: str) -> bool:
        """
        Remove a client from a room.

        Args:
            client_id: Client to remove
            room: Room name to leave

        Returns:
            True if left successfully
        """
        return self._leave_room_internal(client_id, room)

    def _leave_room_internal(self, client_id: str, room: str) -> bool:
        """Internal method to leave a room without async."""
        connection = self._connections.get(client_id)
        if not connection:
            return False

        if room in self._rooms:
            self._rooms[room].discard(client_id)
            if not self._rooms[room]:
                del self._rooms[room]

        connection.rooms.discard(room)
        logger.debug(f"Client {client_id} left room: {room}")
        return True

    async def broadcast_to_room(
        self,
        room: str,
        message: dict | str,
        exclude: set[str] | None = None,
    ) -> int:
        """
        Send a message to all clients in a room.

        Args:
            room: Target room name
            message: Message to send
            exclude: Set of client_ids to exclude

        Returns:
            Number of clients the message was sent to
        """
        exclude = exclude or set()
        sent_count = 0

        client_ids = self._rooms.get(room, set())
        for client_id in list(client_ids):
            if client_id not in exclude:
                if await self.send_personal(client_id, message):
                    sent_count += 1

        # Cross-instance broadcast via Redis
        if settings.ws_redis_url:
            await self._publish(f"room:{room}", message, exclude)

        return sent_count

    def get_room_members(self, room: str) -> set[str]:
        """Get all client IDs in a room."""
        return self._rooms.get(room, set()).copy()

    def get_client_rooms(self, client_id: str) -> set[str]:
        """Get all rooms a client is in."""
        connection = self._connections.get(client_id)
        if not connection:
            return set()
        return connection.rooms.copy()

    @property
    def connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    def is_connected(self, client_id: str) -> bool:
        """Check if a client is connected."""
        return client_id in self._connections

    # =========================================================================
    # Redis Pub/Sub for Multi-Instance Support
    # =========================================================================

    async def start_pubsub(self) -> None:
        """
        Start Redis pub/sub listener for cross-instance messaging.

        Call this in your app's lifespan startup if using multi-instance deployment.
        """
        if not settings.ws_redis_url:
            logger.debug("WS_REDIS_URL not set, skipping pub/sub setup")
            return

        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(settings.ws_redis_url)
            self._redis_pubsub = self._redis.pubsub()

            # Subscribe to broadcast channel
            await self._redis_pubsub.subscribe("ws:broadcast")

            # Start listener task
            self._pubsub_task = asyncio.create_task(self._pubsub_listener())
            logger.info("WebSocket Redis pub/sub started")

        except ImportError:
            logger.warning("redis package not installed, pub/sub disabled")
        except Exception as e:
            logger.error(f"Failed to start Redis pub/sub: {e}")

    async def stop_pubsub(self) -> None:
        """Stop Redis pub/sub listener."""
        if self._pubsub_task:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass

        if self._redis_pubsub:
            await self._redis_pubsub.unsubscribe()
            await self._redis_pubsub.close()

        if hasattr(self, "_redis") and self._redis:
            await self._redis.close()

        logger.info("WebSocket Redis pub/sub stopped")

    async def _pubsub_listener(self) -> None:
        """Listen for messages from Redis pub/sub."""
        try:
            async for message in self._redis_pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data = json.loads(message["data"])
                    channel = data.get("channel", "__broadcast__")
                    payload = data.get("message")
                    exclude = set(data.get("exclude", []))

                    if channel == "__broadcast__":
                        # Broadcast to all local connections
                        for client_id in list(self._connections.keys()):
                            if client_id not in exclude:
                                await self.send_personal(client_id, payload)

                    elif channel.startswith("room:"):
                        room = channel[5:]  # Remove "room:" prefix
                        client_ids = self._rooms.get(room, set())
                        for client_id in list(client_ids):
                            if client_id not in exclude:
                                await self.send_personal(client_id, payload)

                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in pub/sub message")
                except Exception as e:
                    logger.error(f"Error processing pub/sub message: {e}")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Pub/sub listener error: {e}")

    async def _publish(
        self,
        channel: str,
        message: dict | str,
        exclude: set[str] | None = None,
    ) -> None:
        """Publish a message to Redis for cross-instance delivery."""
        if not hasattr(self, "_redis") or not self._redis:
            return

        try:
            data = json.dumps({
                "channel": channel,
                "message": message,
                "exclude": list(exclude or []),
            })
            await self._redis.publish("ws:broadcast", data)
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")


# Global connection manager instance
manager = ConnectionManager()
```

---

## 5. Generated Settings Fields

Added to `settings.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # WebSocket
    ws_redis_url: str = ""  # Optional: for multi-instance pub/sub
    ws_heartbeat_interval: int = 30
```

---

## 6. `.env.example` Additions

```env
# WebSocket
# Leave empty for single-instance (in-memory) mode
# Set for multi-instance deployments with Redis pub/sub
WS_REDIS_URL=
WS_HEARTBEAT_INTERVAL=30

# For multi-instance mode:
# WS_REDIS_URL=redis://localhost:6379/2
```

---

## 7. CLI Integration Updates

Add to `src/paxx/cli/infra.py` after the "Next steps" section:

```python
# Custom guidance for websocket
if name == "websocket":
    console.print("\n[bold]Basic WebSocket endpoint:[/bold]")
    console.print("  [dim]from fastapi import WebSocket, WebSocketDisconnect[/dim]")
    console.print("  [dim]from core.ws import manager[/dim]")
    console.print("")
    console.print("  [dim]@app.websocket('/ws/{client_id}')[/dim]")
    console.print("  [dim]async def websocket_endpoint(websocket: WebSocket, client_id: str):[/dim]")
    console.print("  [dim]    await manager.connect(websocket, client_id)[/dim]")
    console.print("  [dim]    try:[/dim]")
    console.print("  [dim]        while True:[/dim]")
    console.print("  [dim]            data = await websocket.receive_text()[/dim]")
    console.print("  [dim]            await manager.broadcast(data)[/dim]")
    console.print("  [dim]    except WebSocketDisconnect:[/dim]")
    console.print("  [dim]        manager.disconnect(client_id)[/dim]")
    console.print("\n[bold]Multi-instance mode:[/bold]")
    console.print("  Set [bold]WS_REDIS_URL[/bold] and call [dim]await manager.start_pubsub()[/dim] in lifespan")
```

---

## 8. Usage Examples

### Basic WebSocket Endpoint

```python
# features/chat/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.ws import manager

router = APIRouter(prefix="/chat", tags=["chat"])


@router.websocket("/ws/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, user_id)

    try:
        # Join a default room
        await manager.join_room(user_id, "general")

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            match data.get("type"):
                case "message":
                    # Broadcast to room
                    await manager.broadcast_to_room(
                        "general",
                        {
                            "type": "message",
                            "from": user_id,
                            "text": data.get("text"),
                        },
                    )

                case "join_room":
                    room = data.get("room")
                    await manager.join_room(user_id, room)
                    await manager.send_personal(
                        user_id,
                        {"type": "joined", "room": room},
                    )

                case "leave_room":
                    room = data.get("room")
                    await manager.leave_room(user_id, room)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # Notify others
        await manager.broadcast_to_room(
            "general",
            {"type": "user_left", "user_id": user_id},
        )
```

### Authentication with WebSockets

```python
# features/notifications/routes.py
from fastapi import WebSocket, WebSocketDisconnect, Query, status
from core.ws import manager
from core.dependencies import get_current_user_ws


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Authenticated WebSocket for user notifications."""
    # Validate token before accepting connection
    try:
        user = await get_current_user_ws(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, f"user:{user.id}")

    try:
        # Join user-specific room
        await manager.join_room(f"user:{user.id}", f"notifications:{user.id}")

        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_text()

            if data == "ping":
                await manager.send_personal(f"user:{user.id}", "pong")

    except WebSocketDisconnect:
        manager.disconnect(f"user:{user.id}")
```

### Sending Notifications from Background Tasks

```python
# features/orders/services.py
from core.ws import manager


async def process_order(order_id: int, user_id: int) -> None:
    """Process order and notify user via WebSocket."""
    # ... process order ...

    # Send real-time notification to user
    await manager.broadcast_to_room(
        f"notifications:{user_id}",
        {
            "type": "order_update",
            "order_id": order_id,
            "status": "completed",
        },
    )
```

### Live Dashboard Updates

```python
# features/dashboard/routes.py
from fastapi import WebSocket, WebSocketDisconnect
from core.ws import manager


@router.websocket("/ws/dashboard/{dashboard_id}")
async def dashboard_websocket(websocket: WebSocket, dashboard_id: str):
    """Real-time dashboard updates."""
    client_id = f"dashboard:{dashboard_id}:{id(websocket)}"

    await manager.connect(websocket, client_id)
    await manager.join_room(client_id, f"dashboard:{dashboard_id}")

    try:
        while True:
            # Handle subscription changes
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                widget_id = data.get("widget_id")
                await manager.join_room(client_id, f"widget:{widget_id}")

    except WebSocketDisconnect:
        manager.disconnect(client_id)


# Send updates from anywhere in your code
async def update_widget_data(widget_id: str, data: dict):
    """Push widget update to all subscribed clients."""
    await manager.broadcast_to_room(
        f"widget:{widget_id}",
        {"type": "widget_update", "widget_id": widget_id, "data": data},
    )
```

---

## 9. Multi-Instance Setup with Redis Pub/Sub

For horizontally scaled deployments (multiple app instances), enable Redis pub/sub:

### Update Lifespan

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await manager.start_pubsub()
    yield
    # Shutdown
    await manager.stop_pubsub()


app = FastAPI(lifespan=lifespan)
```

### Configure Environment

```env
# .env
WS_REDIS_URL=redis://localhost:6379/2
```

### How It Works

1. Client connects to Instance A
2. Another client connects to Instance B
3. When Instance A broadcasts, it:
   - Sends to all local connections
   - Publishes message to Redis
4. Instance B receives Redis message and:
   - Sends to all its local connections
5. Both clients receive the message

---

## 10. Heartbeat / Keep-Alive

For long-lived connections, implement heartbeat:

```python
# In your WebSocket endpoint
import asyncio


async def websocket_with_heartbeat(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)

    async def heartbeat():
        while True:
            await asyncio.sleep(settings.ws_heartbeat_interval)
            try:
                await websocket.send_json({"type": "ping"})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "pong":
                continue  # Heartbeat response

            # Handle other messages...

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        manager.disconnect(client_id)
```

---

## 11. Implementation Checklist

- [ ] Create `src/paxx/infra/websocket/__init__.py` (empty)
- [ ] Create `src/paxx/infra/websocket/config.py` with InfraConfig
- [ ] Create `src/paxx/infra/websocket/dependencies.txt` (empty or comment)
- [ ] Create `src/paxx/infra/websocket/docker_service.yml` (empty)
- [ ] Create `src/paxx/infra/websocket/templates/ws.py.jinja`
- [ ] Update `src/paxx/cli/infra.py` with websocket-specific guidance
- [ ] Test: `paxx infra add websocket` on fresh project
- [ ] Test: Basic connect/disconnect
- [ ] Test: Broadcast to all clients
- [ ] Test: Room join/leave and room broadcast
- [ ] Test: Multi-instance with Redis pub/sub

---

## 12. Advanced Patterns

### Typing for WebSocket Messages

```python
# core/ws_types.py
from typing import Literal
from pydantic import BaseModel


class WSMessage(BaseModel):
    """Base WebSocket message."""
    type: str


class ChatMessage(WSMessage):
    type: Literal["message"] = "message"
    text: str
    from_user: str


class JoinRoomMessage(WSMessage):
    type: Literal["join_room"] = "join_room"
    room: str


class UserJoinedEvent(WSMessage):
    type: Literal["user_joined"] = "user_joined"
    user_id: str
    room: str


# Usage in routes
async def handle_message(data: dict) -> None:
    msg_type = data.get("type")

    if msg_type == "message":
        msg = ChatMessage(**data)
        # Handle chat message...
```

### Rate Limiting WebSocket Messages

```python
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_messages: int = 10, window_seconds: int = 1):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._counts: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self._counts[client_id] = [
            t for t in self._counts[client_id] if t > window_start
        ]

        if len(self._counts[client_id]) >= self.max_messages:
            return False

        self._counts[client_id].append(now)
        return True


rate_limiter = RateLimiter()


# In WebSocket handler
async def handle_incoming(client_id: str, data: dict):
    if not rate_limiter.is_allowed(client_id):
        await manager.send_personal(
            client_id,
            {"type": "error", "message": "Rate limit exceeded"},
        )
        return

    # Process message...
```

### Connection State Persistence

```python
# Store connection metadata in Redis for recovery
import json


async def connect_with_state(
    websocket: WebSocket,
    client_id: str,
    user_id: int,
) -> None:
    await manager.connect(websocket, client_id)

    # Store connection state in Redis
    if settings.ws_redis_url:
        import redis.asyncio as redis

        r = redis.from_url(settings.ws_redis_url)
        await r.hset(
            f"ws:state:{client_id}",
            mapping={
                "user_id": user_id,
                "connected_at": time.time(),
                "rooms": json.dumps(list(manager.get_client_rooms(client_id))),
            },
        )
        await r.expire(f"ws:state:{client_id}", 86400)  # 24 hour TTL
        await r.close()


async def disconnect_with_cleanup(client_id: str) -> None:
    manager.disconnect(client_id)

    # Clean up state from Redis
    if settings.ws_redis_url:
        import redis.asyncio as redis

        r = redis.from_url(settings.ws_redis_url)
        await r.delete(f"ws:state:{client_id}")
        await r.close()
```

### Broadcasting from HTTP Endpoints

```python
# features/admin/routes.py
from fastapi import APIRouter
from core.ws import manager

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/broadcast")
async def admin_broadcast(message: str):
    """Send a message to all connected clients."""
    count = await manager.broadcast({
        "type": "announcement",
        "message": message,
    })
    return {"sent_to": count}


@router.post("/notify/{user_id}")
async def notify_user(user_id: int, message: str):
    """Send notification to specific user."""
    sent = await manager.send_personal(
        f"user:{user_id}",
        {"type": "notification", "message": message},
    )
    return {"sent": sent}
```

---

## 13. Testing WebSockets

### Using pytest

```python
# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from main import app


def test_websocket_connect():
    client = TestClient(app)

    with client.websocket_connect("/ws/test-client") as websocket:
        # Send a message
        websocket.send_json({"type": "message", "text": "Hello"})

        # Receive response
        data = websocket.receive_json()
        assert data["type"] == "message"


def test_websocket_broadcast():
    client = TestClient(app)

    with client.websocket_connect("/ws/client1") as ws1:
        with client.websocket_connect("/ws/client2") as ws2:
            # Client 1 sends
            ws1.send_json({"type": "message", "text": "Hello"})

            # Both should receive (including sender)
            data1 = ws1.receive_json()
            data2 = ws2.receive_json()

            assert data1["text"] == "Hello"
            assert data2["text"] == "Hello"
```

### Manual Testing with websocat

```bash
# Install websocat
brew install websocat

# Connect to WebSocket
websocat ws://localhost:8000/ws/test-user

# Send JSON messages
{"type": "message", "text": "Hello!"}
```

---

## Summary

The WebSocket implementation provides:

1. **ConnectionManager class** - central hub for managing WebSocket connections
2. **Room/channel support** - group connections for targeted broadcasting
3. **Multi-instance support** - Redis pub/sub for horizontally scaled deployments
4. **Zero extra dependencies** - uses FastAPI's native WebSocket support
5. **Async-first design** - matches Paxx's patterns throughout
6. **Flexible configuration** - works in single-instance mode by default, Redis optional

This enables real-time features like chat, notifications, live dashboards, and collaborative editing without adding complexity to the base template.
