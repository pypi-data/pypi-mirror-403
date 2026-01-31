# Infrastructure

Infrastructure components add system capabilities like caching, object storage, and observability to your paxx project.

For add-ons that enhance existing infrastructure, see [Extensions](extensions.md).

## Overview

```bash
paxx infra list           # List available components
paxx infra add <name>     # Add a component
```

When you add an infrastructure component, paxx:

1. Renders templates to `services/` (e.g., `services/cache.py`)
2. Merges Docker services into `docker-compose.yml`
3. Adds dependencies to `pyproject.toml`
4. Adds environment variables to `settings.py` and `.env.example`

---

## Redis

Async Redis client for caching and pub/sub.

```bash
paxx infra add redis
```

### Generated Files

- `services/cache.py` - Redis client and caching utilities

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |

### Docker Service

Adds Redis 7 Alpine to `docker-compose.yml`.

### Usage

```python
from services.cache import cache_get, cache_set, cache_delete, get_redis

# Simple caching
await cache_set("user:123", {"name": "John"}, expire=3600)
user = await cache_get("user:123")
await cache_delete("user:123")

# Direct Redis access
redis = await get_redis()
await redis.incr("page_views")
```

### Dependency

- `redis>=5.0`

---

## Storage

Object storage supporting local filesystem and S3-compatible backends (AWS S3, MinIO).

```bash
paxx infra add storage
```

### Generated Files

- `services/storage.py` - Storage abstraction and backends

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STORAGE_BACKEND` | `local` | Storage backend (`local` or `s3`) |
| `STORAGE_LOCAL_PATH` | `./uploads` | Local storage path |
| `STORAGE_S3_BUCKET` | - | S3 bucket name |
| `STORAGE_S3_REGION` | `us-east-1` | S3 region |
| `STORAGE_S3_ENDPOINT_URL` | - | Custom S3 endpoint (for MinIO) |
| `STORAGE_S3_ACCESS_KEY` | - | S3 access key |
| `STORAGE_S3_SECRET_KEY` | - | S3 secret key |

### Docker Service

Adds MinIO service for local S3-compatible testing.

### Usage

```python
from services.storage import get_storage

storage = get_storage()

# Upload a file
url = await storage.upload("images/photo.jpg", file_data)

# Download a file
data = await storage.download("images/photo.jpg")

# Delete a file
await storage.delete("images/photo.jpg")

# Check if file exists
exists = await storage.exists("images/photo.jpg")
```

### MinIO Testing

1. Start MinIO:
   ```bash
   docker compose up -d minio
   ```

2. Open console at http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

3. Create a bucket

4. Configure environment:
   ```bash
   STORAGE_BACKEND=s3
   STORAGE_S3_BUCKET=my-bucket
   STORAGE_S3_ENDPOINT_URL=http://localhost:9000
   STORAGE_S3_ACCESS_KEY=minioadmin
   STORAGE_S3_SECRET_KEY=minioadmin
   ```

### Dependencies

- `aioboto3>=13.0`
- `aiofiles>=24.0`

---

## Metrics

Prometheus metrics and OpenTelemetry distributed tracing.

```bash
paxx infra add metrics
```

### Generated Files

- `services/metrics.py` - Prometheus metrics setup
- `services/tracing.py` - OpenTelemetry tracing setup

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_SERVICE_NAME` | `myapp` | Service name for tracing |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP endpoint |
| `METRICS_ENABLED` | `true` | Enable/disable metrics |

### Docker Service

Adds Jaeger for local trace visualization.

### Prometheus Metrics

```python
from services.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    ACTIVE_REQUESTS,
)

# Metrics are automatically collected via middleware
# Access at /metrics endpoint
```

Built-in metrics:
- `http_requests_total` - Total HTTP requests (labels: method, path, status)
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Currently processing requests

### OpenTelemetry Tracing

Automatic instrumentation for:
- FastAPI requests
- SQLAlchemy queries
- HTTP client requests

View traces in Jaeger:

```bash
docker compose up -d jaeger
# Open http://localhost:16686
```

### Custom Spans

```python
from services.tracing import get_tracer

tracer = get_tracer(__name__)

async def process_order(order_id: int):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        # Your logic here
```

### Dependencies

- `opentelemetry-api>=1.20`
- `opentelemetry-sdk>=1.20`
- `opentelemetry-instrumentation-fastapi>=0.41b0`
- `opentelemetry-instrumentation-sqlalchemy>=0.41b0`
- `opentelemetry-exporter-otlp>=1.20`
- `prometheus-client>=0.19`

---

## Summary

| Component | Purpose | Docker Service | Key Files |
|-----------|---------|----------------|-----------|
| **redis** | Caching, pub/sub | Redis | `services/cache.py` |
| **storage** | Object storage | MinIO | `services/storage.py` |
| **metrics** | Observability | Jaeger | `services/metrics.py`, `coservicesre/tracing.py` |

See also: [Extensions](extensions.md) for add-ons like ARQ, WebSocket, and PostGIS.

## Best Practices

1. **Start with what you need** - Add components as requirements emerge
2. **Development vs Production** - Docker services are for local development; configure production services separately
3. **Environment variables** - Always configure production values via environment variables, not in code
4. **Dependencies** - Run `uv sync` after adding infrastructure to install new dependencies

## Next Steps

[Extend](extensions.md) exisitng app with websockets support, postGIS and more
