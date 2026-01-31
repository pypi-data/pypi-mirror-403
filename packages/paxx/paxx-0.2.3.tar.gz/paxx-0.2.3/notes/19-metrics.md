# Metrics & Tracing Implementation Plan

## Overview

Add observability infrastructure to paxx following the existing `infra/` pattern. Provides OpenTelemetry tracing and Prometheus metrics with minimal configuration.

---

## Structure

```
src/paxx/infra/metrics/
├── __init__.py
├── config.py
├── dependencies.txt
├── docker_service.yml          # Jaeger all-in-one for dev
└── templates/
    ├── metrics.py.jinja        # Prometheus metrics setup
    └── tracing.py.jinja        # OpenTelemetry setup
```

---

## Components

### 1. `config.py`

```python
from dataclasses import dataclass, field

@dataclass
class InfraConfig:
    name: str = "metrics"
    docker_service: str = "jaeger"
    core_files: list[str] = field(default_factory=lambda: ["metrics.py", "tracing.py"])
    dependencies: list[str] = field(default_factory=lambda: [
        "opentelemetry-api",
        "opentelemetry-sdk",
        "opentelemetry-instrumentation-fastapi",
        "opentelemetry-instrumentation-sqlalchemy",
        "opentelemetry-exporter-otlp",
        "prometheus-client",
    ])
    env_vars: dict[str, str] = field(default_factory=lambda: {
        "OTEL_SERVICE_NAME": "{{ project_name }}",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        "METRICS_ENABLED": "true",
    })
```

### 2. `dependencies.txt`

```
opentelemetry-api>=1.20
opentelemetry-sdk>=1.20
opentelemetry-instrumentation-fastapi>=0.41b0
opentelemetry-instrumentation-sqlalchemy>=0.41b0
opentelemetry-exporter-otlp>=1.20
prometheus-client>=0.19
```

### 3. `docker_service.yml`

```yaml
jaeger:
  image: jaegertracing/all-in-one:1.54
  ports:
    - "16686:16686"   # Jaeger UI
    - "4317:4317"     # OTLP gRPC receiver
  environment:
    - COLLECTOR_OTLP_ENABLED=true
  healthcheck:
    test: ["CMD", "wget", "--spider", "-q", "http://localhost:16686"]
    interval: 10s
    timeout: 5s
    retries: 3
```

### 4. `templates/tracing.py.jinja`

OpenTelemetry initialization with auto-instrumentation:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from settings import settings


def init_tracing(app, engine=None):
    """Initialize OpenTelemetry tracing."""
    if not settings.metrics_enabled:
        return

    resource = Resource(attributes={
        SERVICE_NAME: settings.otel_service_name
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)

    # Auto-instrument SQLAlchemy if engine provided
    if engine:
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def get_tracer(name: str):
    """Get a tracer for custom spans."""
    return trace.get_tracer(name)
```

### 5. `templates/metrics.py.jinja`

Prometheus metrics with FastAPI integration:

```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
import time

from settings import settings


# Standard metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics."""

    async def dispatch(self, request: Request, call_next):
        if not settings.metrics_enabled:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start_time

        endpoint = request.url.path
        method = request.method
        status = response.status_code

        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

        return response


async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## Usage in Generated Project

### Lifespan Integration

```python
# main.py
from contextlib import asynccontextmanager
from core.tracing import init_tracing
from core.metrics import MetricsMiddleware, metrics_endpoint

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_tracing(app, engine=engine)
    yield

app = create_app()
app.add_middleware(MetricsMiddleware)
app.add_route("/metrics", metrics_endpoint)
```

### Custom Spans

```python
from core.tracing import get_tracer

tracer = get_tracer(__name__)

async def process_order(order_id: str):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        # ... business logic
```

### Custom Metrics

```python
from prometheus_client import Counter

ORDERS_PROCESSED = Counter("orders_processed_total", "Total orders processed", ["status"])

async def complete_order(order):
    # ... logic
    ORDERS_PROCESSED.labels(status="completed").inc()
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| OpenTelemetry over vendor-specific | Industry standard, works with Jaeger/Tempo/Datadog/Honeycomb |
| Jaeger for dev | Simple all-in-one container, good UI |
| OTLP export | Universal protocol, switch backends without code changes |
| Prometheus for metrics | Standard, works with Grafana, cheap to scrape |
| Auto-instrumentation | Zero-code changes for basic traces |
| `METRICS_ENABLED` flag | Disable for local dev to reduce overhead |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_SERVICE_NAME` | `{{ project_name }}` | Service name in traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |
| `METRICS_ENABLED` | `true` | Enable/disable metrics & tracing |

---

## Production Considerations

### Grafana Cloud / Tempo
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://tempo-us-central1.grafana.net:443
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64-credentials>
```

### Datadog
```bash
# Use Datadog agent as OTLP collector
OTEL_EXPORTER_OTLP_ENDPOINT=http://datadog-agent:4317
```

### Self-hosted
```yaml
# Add to docker-compose for production
otel-collector:
  image: otel/opentelemetry-collector-contrib:latest
  command: ["--config=/etc/otel-config.yaml"]
  volumes:
    - ./otel-config.yaml:/etc/otel-config.yaml
```

---

## CLI Command

```bash
paxx infra add metrics
```

This will:
1. Create `core/tracing.py` and `core/metrics.py`
2. Add Jaeger service to `docker-compose.yml`
3. Add dependencies to `pyproject.toml`
4. Add env vars to `settings.py` and `.env.example`
