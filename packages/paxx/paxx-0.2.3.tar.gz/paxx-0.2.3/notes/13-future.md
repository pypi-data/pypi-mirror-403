# Paxx Future Enhancements

Ideas for additional components to make app creation faster while keeping paxx general and flexible.

---

## Tier 1: High-Value, Common Needs (ALL IMPLEMENTED)

### Redis [IMPLEMENTED]
- **Why**: Caching, sessions, rate limiting, pub/sub
- **Implementation**: Optional service in docker-compose. Create `core/cache.py` with async redis client (aioredis/redis-py async)
- **Priority**: High - many apps need this

### Background Tasks [IMPLEMENTED]
- **Why**: Email sending, webhooks, heavy processing, scheduled jobs
- **Options**:
  - **ARQ** (recommended) - async Redis queue, lightweight, Python-native
  - **Dramatiq** - good middle ground
  - **Celery** - heavy, but battle-tested
  - **FastAPI BackgroundTasks** - for trivial cases only
- **Implementation**: ARQ worker with task decorators, redis as broker
- **Priority**: High

### Object Storage (S3) [IMPLEMENTED]
- **Why**: File uploads, media, user-generated content
- **Implementation**:
  - Abstract `StorageBackend` interface in `core/storage.py`
  - Local filesystem backend for dev
  - S3-compatible backend for production
  - **MinIO** in docker-compose for local S3-compatible testing
- **Priority**: High

### WebSockets [IMPLEMENTED]
- **Why**: Real-time updates, notifications, chat, live dashboards
- **Implementation**:
  - FastAPI has native WebSocket support
  - `core/ws.py` with ConnectionManager class
  - Room/channel support for broadcasting
  - Integration with Redis pub/sub for multi-instance
- **Priority**: High

---

## Tier 2: Specialized but Valuable

### Vector Database
- **Why**: AI/ML apps, embeddings, semantic search
- **Options**:
  - **pgvector** (recommended) - PostgreSQL extension, no new infra
  - Pinecone, Weaviate, Qdrant - if truly need scale
- **Implementation**: Enable pgvector extension, add embedding utilities
- **Priority**: Medium - only for AI-focused apps

### Email Service
- **Why**: Transactional emails, notifications, password resets
- **Implementation**:
  - `core/email.py` with async interface
  - Template support (Jinja2)
  - Backends: SMTP, SendGrid, Postmark, Resend
- **Priority**: Medium-High - almost every app needs this

### Full-Text Search
- **Why**: Search functionality beyond simple LIKE queries
- **Options**:
  - PostgreSQL FTS - often sufficient, no extra infra
  - **Meilisearch** or **Typesense** - for heavier needs, great DX
  - Elasticsearch - powerful but complex
- **Implementation**: Start with PostgreSQL FTS, add Meilisearch as optional
- **Priority**: Medium

### MongoDB
- **Why**: Document store, flexible schemas, JSON-heavy workloads
- **Reality**: Most apps don't need it alongside PostgreSQL. PostgreSQL JSONB columns often suffice.
- **Implementation**: Optional, only if truly document-oriented
- **Priority**: Low - be cautious about adding DB complexity

---

## Tier 3: Infrastructure & DevEx

### Rate Limiting
- **Why**: API protection, abuse prevention
- **Implementation**: Redis-backed + `slowapi` or custom middleware
- **Priority**: Medium

### Feature Flags
- **Why**: Gradual rollouts, A/B testing, kill switches
- **Implementation**: Simple DB or Redis-backed flag system
- **Priority**: Low-Medium

### Metrics & Tracing
- **Why**: Observability, debugging, performance monitoring
- **Implementation**:
  - OpenTelemetry integration
  - Prometheus metrics endpoint (`/metrics`)
  - Optional Jaeger/Zipkin for tracing
- **Priority**: Medium for production apps

### GraphQL
- **Why**: Alternative API style, flexible queries
- **Implementation**: Strawberry as optional layer on existing services
- **Priority**: Low - REST is fine for most cases

---

## Recommended Implementation Plan

### Phase 1: Core Infrastructure
```
paxx feature add redis      # Cache, sessions, rate limiter
paxx feature add tasks      # ARQ worker, task definitions
paxx feature add storage    # S3/MinIO abstraction
paxx feature add email      # Transactional email service
```

### Phase 2: Real-Time & AI
```
paxx feature add websocket  # WS manager, rooms, Redis pub/sub
paxx feature add vector     # pgvector extension, embeddings
```

### Phase 3: DevEx & Ops
```
paxx feature add metrics    # Prometheus, OpenTelemetry
paxx feature add search     # PostgreSQL FTS or Meilisearch
```

Each feature should be:
- **Optional** - only added when needed
- **Composable** - works independently or together
- **Docker-integrated** - adds services to docker-compose when needed
- **Well-documented** - clear usage examples

---

## What to Avoid

### Don't Add
- **Too many database options** - PostgreSQL + Redis covers 95% of cases
- **Heavy orchestration** (Kubernetes configs, etc.) - keep it single-process friendly
- **Framework lock-in** - thin abstractions, swappable implementations
- **Kafka/RabbitMQ** - overkill unless building event-driven microservices

### Design Principles
- **Lightweight by default** - don't bloat the base template
- **Progressive complexity** - easy to add what you need
- **Production-ready** - each component should be deployable
- **Async-first** - all new components should use async patterns

---

## CLI Commands Vision

```bash
# List available features
paxx feature list

# Add specific features
paxx feature add redis
paxx feature add tasks
paxx feature add storage
paxx feature add email
paxx feature add websocket
paxx feature add vector
paxx feature add metrics

# Features update docker-compose.yml automatically
# Features add necessary dependencies to pyproject.toml
# Features create core/ modules with sensible defaults
```

---

## Summary

**Must-Have** (Phase 1) - COMPLETED:
1. Redis - caching, sessions, rate limiting [IMPLEMENTED]
2. Background Tasks (ARQ) - async job processing [IMPLEMENTED]
3. Object Storage - S3-compatible file handling [IMPLEMENTED]
4. WebSocket Manager - real-time capabilities [IMPLEMENTED]

**Should-Have** (Phase 2):
5. Email - transactional email service
6. pgvector - vector search without new infra

**Nice-to-Have** (Phase 3):
7. Metrics/Tracing - observability
8. Full-text Search - PostgreSQL FTS or Meilisearch

This keeps paxx general and flexible while making common patterns easy to adopt.
