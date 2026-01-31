# Next Steps (January 2026)

## Paxx CLI Feature Ideas

### High-Value Additions

1. **Authentication** - JWT, OAuth2/social login, API keys, RBAC permissions (most APIs need this)
2. **Email** - Transactional email with templates (SendGrid, SES, SMTP)
3. **Admin panel** - SQLAdmin or similar for quick data management
4. **Rate limiting** - API throttling middleware
5. **Scheduled tasks** - Cron-like jobs (extend arq or add APScheduler)

### Infrastructure Components

- **Search** - Elasticsearch, Meilisearch, or Typesense
- **Message queues** - Kafka, RabbitMQ for event-driven patterns
- **Circuit breakers** - Resilience for external service calls

### Deploy Targets

- Kubernetes (Helm charts)
- Cloud-specific: AWS ECS/Fargate, GCP Cloud Run
- PaaS: Fly.io, Railway, Render

### Developer Experience

- **Test factories** - Factory Boy or Polyfactory for test data
- **CLI for generated app** - Management commands (like Django's manage.py)
- **API versioning** - v1/v2 endpoint scaffolding
- **OpenAPI export** - Generate client SDKs

### Enterprise Features

- Multi-tenancy (schema-per-tenant or row-level)
- Audit logging
- Feature flags

---

## Prioritized Recommendations

Based on reviewing all notes, here's a prioritized roadmap:

### What's Done

All Tier 1 infra is complete: Redis, ARQ, Storage, WebSocket, PostGIS, Metrics. Core scaffolding and deployment are solid.

### 1. Polish First (Low Effort, High ROI)

- **Extract `cli/utils.py`** (14-code-review.md) — ~100 lines of duplicated code across bootstrap.py, feature.py, deploy.py. Quick win for maintainability.
- **Fix deploy add output text** (todo.md) — small UX issue noted.

### 2. Generated Project Improvements

These make every bootstrapped app better without adding new features:

- **Pre-commit hooks config** — ruff + mypy, dependency already exists
- **Security headers middleware** — standard protection, straightforward
- **Enforce SECRET_KEY in production** — one-line fix, prevents prod accidents

### 3. Authentication (High Value)

This is the obvious next big feature. Almost every API needs it, and it's tedious to set up correctly. Could include:

- JWT with refresh tokens
- OAuth2 social login (Google, GitHub)
- API keys for machine clients
- RBAC/permissions helpers

This would be `paxx infra add auth` or `paxx feature add auth`.

### 4. Email Service

Second most common need after auth. Transactional emails for password resets, notifications, etc. Pluggable backends (SMTP, SendGrid, Resend).

---

## Summary

**Suggested order:**

1. Utils refactor + deploy text fix (quick wins)
2. Generated project polish (pre-commit, security headers, SECRET_KEY enforcement)
3. Authentication — highest-impact new feature
4. Email — follows naturally since auth often needs it for password resets

The geo-app analysis (21-geo-app-support.md) shows infra coverage is already excellent for real projects. Auth is the main gap.
