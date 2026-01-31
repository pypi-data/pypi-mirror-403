# ARQ Background Tasks Implementation Plan

Background task processing using ARQ (async Redis queue) for Paxx-generated projects.

---

## Overview

ARQ is a lightweight, async-first job queue built on Redis. It's the recommended choice for Paxx because:
- Python-native with full async/await support
- Minimal dependencies (just Redis)
- Built-in retry logic, timeouts, and job results
- Cron-like scheduled tasks
- Simple API with decorators

---

## Implementation Structure

```
src/paxx/infra/arq/
├── __init__.py
├── config.py
├── dependencies.txt
├── docker_service.yml          # Empty - reuses Redis
└── templates/
    ├── arq.py.jinja            # ARQ connection pool & enqueue helpers
    └── tasks.py.jinja          # Task definitions & worker config
```

---

## 1. Config (`config.py`)

```python
"""ARQ background tasks infrastructure configuration."""

from dataclasses import dataclass, field


@dataclass
class InfraConfig:
    """Configuration for ARQ task queue infrastructure."""

    name: str = "arq"
    docker_service: str = ""  # Reuses existing Redis service
    core_files: list[str] = field(default_factory=lambda: ["arq.py", "tasks.py"])
    dependencies: list[str] = field(default_factory=lambda: ["arq>=0.26"])
    env_vars: dict[str, str] = field(
        default_factory=lambda: {
            "ARQ_REDIS_URL": "redis://localhost:6379/1",
            "ARQ_MAX_JOBS": "10",
            "ARQ_JOB_TIMEOUT": "300",
        }
    )
```

**Notes:**
- Uses Redis DB 1 to isolate from cache (DB 0)
- `ARQ_MAX_JOBS` controls worker concurrency
- `ARQ_JOB_TIMEOUT` is default timeout per job in seconds

---

## 2. Dependencies (`dependencies.txt`)

```
arq>=0.26
```

---

## 3. Docker Service (`docker_service.yml`)

Empty file - ARQ reuses the Redis service. The `infra.py` already handles missing docker services gracefully.

If Redis hasn't been added, users will see guidance to add it first.

---

## 4. ARQ Template (`templates/arq.py.jinja`)

```python
"""ARQ task queue connection and utilities."""

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from settings import settings

_pool: ArqRedis | None = None


def get_redis_settings() -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    from urllib.parse import urlparse

    parsed = urlparse(settings.arq_redis_url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or 0),
        password=parsed.password,
    )


async def get_pool() -> ArqRedis:
    """Get or create ARQ Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(get_redis_settings())
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def enqueue(
    function: str,
    *args,
    _job_id: str | None = None,
    _defer_by: float | None = None,
    **kwargs,
):
    """
    Enqueue a task for background processing.

    Args:
        function: Name of the task function (e.g., "send_email")
        *args: Positional arguments for the task
        _job_id: Optional custom job ID (for deduplication)
        _defer_by: Optional delay in seconds before execution
        **kwargs: Keyword arguments for the task

    Returns:
        Job object with job_id attribute
    """
    pool = await get_pool()
    job = await pool.enqueue_job(
        function,
        *args,
        _job_id=_job_id,
        _defer_by=_defer_by,
        **kwargs,
    )
    return job


async def get_job_status(job_id: str) -> dict | None:
    """
    Get status of a job by ID.

    Returns dict with keys: function, args, kwargs, job_try, enqueue_time,
    score (scheduled time), success, result, start_time, finish_time
    """
    pool = await get_pool()
    job = await pool.job(job_id)
    if job is None:
        return None
    return await job.info()
```

---

## 5. Tasks Template (`templates/tasks.py.jinja`)

```python
"""
Background task definitions.

Usage:
    # Enqueue a task from your routes/services:
    from core.arq import enqueue
    await enqueue("send_welcome_email", user_id=123)

    # Run the worker:
    uv run arq core.tasks.WorkerSettings
"""

import asyncio
import logging
from datetime import datetime

from arq import cron
from settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Task Functions
# =============================================================================


async def send_welcome_email(ctx: dict, user_id: int) -> dict:
    """
    Example task: Send welcome email to a user.

    Args:
        ctx: ARQ context dict (contains redis connection, job_id, etc.)
        user_id: ID of the user to email

    Returns:
        Result dict (stored in Redis, retrievable via job.result())
    """
    logger.info(f"Sending welcome email to user {user_id}")

    # Simulate email sending
    await asyncio.sleep(1)

    return {"status": "sent", "user_id": user_id, "sent_at": datetime.utcnow().isoformat()}


async def process_webhook(ctx: dict, payload: dict, retry_count: int = 0) -> dict:
    """
    Example task: Process incoming webhook with retry logic.

    Args:
        ctx: ARQ context dict
        payload: Webhook payload to process
        retry_count: Number of retries attempted

    Returns:
        Processing result
    """
    logger.info(f"Processing webhook (attempt {retry_count + 1})")

    # Your webhook processing logic here
    # If it fails, ARQ will retry based on WorkerSettings.max_tries

    return {"processed": True, "attempt": retry_count + 1}


# =============================================================================
# Scheduled Tasks (Cron)
# =============================================================================


async def cleanup_expired_sessions(ctx: dict) -> int:
    """
    Example cron task: Clean up expired sessions.

    Runs daily at 3:00 AM (configured in WorkerSettings.cron_jobs).

    Returns:
        Number of sessions cleaned up
    """
    logger.info("Running scheduled session cleanup")

    # Your cleanup logic here
    cleaned_count = 0

    logger.info(f"Cleaned up {cleaned_count} expired sessions")
    return cleaned_count


# =============================================================================
# Worker Startup/Shutdown
# =============================================================================


async def startup(ctx: dict) -> None:
    """Called when worker starts up."""
    logger.info("ARQ worker starting up")
    # Initialize any resources (DB connections, etc.)


async def shutdown(ctx: dict) -> None:
    """Called when worker shuts down."""
    logger.info("ARQ worker shutting down")
    # Clean up resources


# =============================================================================
# Worker Settings
# =============================================================================


class WorkerSettings:
    """
    ARQ worker configuration.

    Run with: uv run arq core.tasks.WorkerSettings
    """

    from core.arq import get_redis_settings

    redis_settings = get_redis_settings()

    # Register task functions
    functions = [
        send_welcome_email,
        process_webhook,
    ]

    # Cron jobs (scheduled tasks)
    cron_jobs = [
        cron(cleanup_expired_sessions, hour=3, minute=0),  # Daily at 3:00 AM
    ]

    # Worker behavior
    max_jobs = int(settings.arq_max_jobs)
    job_timeout = int(settings.arq_job_timeout)
    max_tries = 3
    retry_delay = 10  # seconds between retries

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown
```

---

## 6. Generated Settings Fields

Added to `settings.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # Infrastructure
    arq_redis_url: str = "redis://localhost:6379/1"
    arq_max_jobs: int = 10
    arq_job_timeout: int = 300
```

---

## 7. CLI Integration Updates

Add to `src/paxx/cli/infra.py` after the "Next steps" section (around line 350):

```python
# Custom guidance for arq
if name == "arq":
    console.print("\n[bold]Running the worker:[/bold]")
    console.print("  [dim]uv run arq core.tasks.WorkerSettings[/dim]")
    console.print("\n[bold]Enqueue tasks from your code:[/bold]")
    console.print("  [dim]from core.arq import enqueue[/dim]")
    console.print("  [dim]await enqueue('send_welcome_email', user_id=123)[/dim]")
```

---

## 8. Usage Examples

### Enqueue from Routes

```python
# features/users/routes.py
from core.arq import enqueue

@router.post("/users")
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Create user in database
    new_user = await user_service.create(db, user)

    # Send welcome email in background
    await enqueue("send_welcome_email", user_id=new_user.id)

    return new_user
```

### Enqueue with Options

```python
from core.arq import enqueue

# Delay execution by 60 seconds
await enqueue("send_reminder", user_id=123, _defer_by=60)

# Custom job ID for deduplication
await enqueue("sync_user", user_id=123, _job_id=f"sync-user-{123}")
```

### Check Job Status

```python
from core.arq import enqueue, get_job_status

# Enqueue and get job reference
job = await enqueue("process_data", data=payload)
print(f"Job ID: {job.job_id}")

# Later, check status
status = await get_job_status(job.job_id)
if status and status.get("success"):
    print(f"Result: {status['result']}")
```

---

## 9. Running the Worker

Development:
```bash
# Watch mode - auto-restart on code changes
uv run arq core.tasks.WorkerSettings --watch
```

Production:
```bash
# Run worker (typically managed by supervisor/systemd)
uv run arq core.tasks.WorkerSettings
```

Docker Compose (add to docker-compose.yml):
```yaml
services:
  worker:
    build: .
    command: arq core.tasks.WorkerSettings
    environment:
      - ARQ_REDIS_URL=redis://redis:6379/1
    depends_on:
      redis:
        condition: service_healthy
```

---

## 10. Implementation Checklist

- [ ] Create `src/paxx/infra/arq/__init__.py` (empty)
- [ ] Create `src/paxx/infra/arq/config.py` with InfraConfig
- [ ] Create `src/paxx/infra/arq/dependencies.txt`
- [ ] Create `src/paxx/infra/arq/docker_service.yml` (empty)
- [ ] Create `src/paxx/infra/arq/templates/arq.py.jinja`
- [ ] Create `src/paxx/infra/arq/templates/tasks.py.jinja`
- [ ] Update `src/paxx/cli/infra.py` with arq-specific guidance
- [ ] Test: `paxx infra add arq` on fresh project
- [ ] Test: Enqueue task from route
- [ ] Test: Run worker and verify task execution
- [ ] Test: Cron job scheduling

---

## 11. Prerequisites Check

The `infra.py` should verify Redis is available. Options:

1. **Auto-add Redis** - If arq is added without Redis, add Redis first
2. **Warn and continue** - Print warning that Redis is required
3. **Error and exit** - Require `paxx infra add redis` first

Recommended: Option 2 (warn) - keeps it flexible for users who have external Redis.

Add check in `infra.py` `add()` command:

```python
if name == "arq":
    # Check if Redis is configured
    settings_path = project_context.project_root / "settings.py"
    settings_content = settings_path.read_text()
    if "redis_url" not in settings_content.lower():
        console.print(
            "[yellow]Note:[/yellow] ARQ requires Redis. "
            "Run [bold]paxx infra add redis[/bold] or configure ARQ_REDIS_URL."
        )
```

---

## 12. Advanced Patterns

### Task with Database Access

```python
# core/tasks.py
from db.database import async_session

async def sync_user_data(ctx: dict, user_id: int) -> dict:
    """Task that needs database access."""
    async with async_session() as session:
        # Your database operations
        user = await session.get(User, user_id)
        # Process...
    return {"synced": True}
```

### Chained Tasks

```python
async def step_one(ctx: dict, data: dict) -> dict:
    result = process(data)
    # Enqueue next step
    from core.arq import enqueue
    await enqueue("step_two", result=result)
    return result

async def step_two(ctx: dict, result: dict) -> dict:
    return finalize(result)
```

### Priority Queues

For different priority levels, run multiple workers with queue names:

```python
# High priority queue
class HighPriorityWorkerSettings(WorkerSettings):
    queue_name = "high"

# Default queue
class WorkerSettings:
    queue_name = "default"
```

Enqueue to specific queue:
```python
from core.arq import enqueue

await enqueue("urgent_task", _queue_name="high", data=payload)
```

---

## Summary

ARQ provides a clean, async-native background task system that integrates well with FastAPI and Paxx's patterns. The implementation:

1. Reuses Redis infrastructure (no new services)
2. Follows Paxx's infra component pattern exactly
3. Provides sensible defaults with full configurability
4. Includes examples for common patterns (email, webhooks, cron)
5. Works seamlessly with existing database and settings patterns
