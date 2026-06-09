# Production Reliability Additions

This project now includes a platform reliability layer that turns the FP&A app into a stronger product-company resume project.

## Implemented Capabilities

- Idempotent API workflow for planning job creation using `Idempotency-Key`, request hashing, replay detection, and conflict handling.
- Reliable outbox pattern for async planning events, with pending/processed state, retry metadata, worker ownership, and Celery draining.
- Distributed lock abstraction using Redis `SET NX EX` with Postgres advisory lock fallback.
- Postgres/TimescaleDB capacity observability for database size, active connections, time-series row volume, and pending outbox backlog.
- Readiness checks for Postgres and Redis dependencies.
- TimescaleDB partition reporting for the `financial_metrics` hypertable.
- Unit tests for deterministic hashing and idempotent replay semantics.

## Resume Bullets

- Built production reliability primitives for a FastAPI, Postgres/TimescaleDB, Redis, and Celery FP&A platform, including idempotent job APIs, distributed locking, and transactional outbox processing.
- Implemented database capacity management APIs tracking Postgres size, connection pressure, TimescaleDB financial metric volume, and async backlog health.
- Designed fault-tolerant async planning workflow with Celery primary delivery and durable outbox fallback to prevent duplicate or lost planning jobs.
- Added readiness and partition observability endpoints to support cloud-style operations, reliability monitoring, and scale diagnostics.

## Interview Talking Points

- Idempotency prevents duplicate planning jobs when clients retry after timeouts.
- The outbox pattern makes job creation durable before async processing starts.
- Redis locks are fast for distributed workers, while Postgres advisory locks provide a database-native fallback.
- TimescaleDB hypertables partition financial time-series data by period, which improves retention, scan efficiency, and operational observability.
- Capacity endpoints model Azure-style thinking: monitor resource limits before they become customer-facing reliability incidents.

## Useful Endpoints

- `GET /platform/ready`
- `GET /platform/capacity`
- `GET /platform/partitions`
- `POST /platform/planning-jobs` with `Idempotency-Key`
- `POST /platform/outbox/drain`
