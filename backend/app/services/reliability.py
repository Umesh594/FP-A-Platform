import hashlib
import json
import socket
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable

import redis
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.logger import logger
from app.models.advanced import CapacitySnapshot, IdempotencyRecord, OutboxEvent


LOCK_TTL_SECONDS = 60
IDEMPOTENCY_TTL_MINUTES = 30


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def json_safe(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, default=str))


def redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)


@contextmanager
def distributed_lock(db: Session, name: str, ttl_seconds: int = LOCK_TTL_SECONDS):
    """
    Cross-process lock with Redis as the fast path and Postgres advisory locks as fallback.
    This keeps scheduled/async workers from running duplicate critical sections.
    """
    owner = f"{socket.gethostname()}:{time.time_ns()}"
    redis_key = f"fpa:lock:{name}"
    acquired = False
    lock_backend = "redis"
    fallback_lock_id = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:15], 16)

    try:
        try:
            acquired = bool(redis_client().set(redis_key, owner, nx=True, ex=ttl_seconds))
        except Exception as exc:
            logger.warning(f"Redis lock unavailable for {name}; using Postgres advisory lock: {exc}")
            lock_backend = "postgres"
            acquired = bool(
                db.execute(text("SELECT pg_try_advisory_lock(:lock_id)"), {"lock_id": fallback_lock_id}).scalar()
            )

        yield acquired
    finally:
        if acquired and lock_backend == "postgres":
            db.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": fallback_lock_id})
            db.commit()
        elif acquired:
            try:
                client = redis_client()
                if client.get(redis_key) == owner.encode("utf-8"):
                    client.delete(redis_key)
            except Exception:
                logger.warning(f"Failed to release Redis lock {name}; it will expire by TTL")


def run_idempotent(
    db: Session,
    *,
    endpoint: str,
    idempotency_key: str,
    request_payload: dict[str, Any],
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    request_hash = canonical_hash(request_payload)
    now = datetime.utcnow()
    record = db.query(IdempotencyRecord).filter_by(idempotency_key=idempotency_key).one_or_none()

    if record:
        if record.request_hash != request_hash:
            return {
                "status": "conflict",
                "message": "Idempotency key reused with a different request payload",
            }
        if record.status == "completed":
            return {
                "status": "replayed",
                "idempotency_key": idempotency_key,
                "response": record.response_payload,
            }
        if record.locked_until > now:
            return {
                "status": "processing",
                "idempotency_key": idempotency_key,
                "message": "Request is already being processed",
            }

    if not record:
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            endpoint=endpoint,
            locked_until=now + timedelta(minutes=IDEMPOTENCY_TTL_MINUTES),
        )
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return run_idempotent(
                db,
                endpoint=endpoint,
                idempotency_key=idempotency_key,
                request_payload=request_payload,
                operation=operation,
            )

    try:
        response = json_safe(operation())
        record.status = "completed"
        record.response_payload = response
        record.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "created", "idempotency_key": idempotency_key, "response": response}
    except Exception:
        db.rollback()
        record = db.query(IdempotencyRecord).filter_by(idempotency_key=idempotency_key).one_or_none()
        if record:
            record.status = "failed"
            record.updated_at = datetime.utcnow()
            db.commit()
        raise


def enqueue_outbox_event(
    db: Session,
    *,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> OutboxEvent:
    event = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event_type,
        payload=payload,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def drain_outbox(db: Session, *, batch_size: int = 10, worker_id: str | None = None) -> dict[str, Any]:
    worker = worker_id or f"{socket.gethostname()}:{time.time_ns()}"
    now = datetime.utcnow()
    processed: list[int] = []
    failed: list[int] = []

    with distributed_lock(db, "outbox-drain", ttl_seconds=30) as acquired:
        if not acquired:
            return {"status": "locked", "processed": [], "failed": []}

        events = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending", OutboxEvent.next_attempt_at <= now)
            .order_by(OutboxEvent.created_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
            .all()
        )

        for event in events:
            event.locked_by = worker
            event.locked_until = now + timedelta(seconds=30)
            event.attempts += 1
            try:
                logger.info(f"Publishing outbox event {event.id}:{event.event_type}")
                event.status = "processed"
                event.processed_at = datetime.utcnow()
                processed.append(event.id)
            except Exception as exc:
                event.status = "pending"
                event.next_attempt_at = datetime.utcnow() + timedelta(seconds=min(300, 2**event.attempts))
                event.last_error = str(exc)
                failed.append(event.id)

        db.commit()

    return {"status": "ok", "processed": processed, "failed": failed}


def database_capacity_report(db: Session) -> dict[str, Any]:
    db_size = db.execute(text("SELECT pg_database_size(current_database())")).scalar() or 0
    active_connections = db.execute(
        text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
    ).scalar() or 0
    max_connections = int(db.execute(text("SHOW max_connections")).scalar() or 0)
    financial_rows = db.execute(text("SELECT count(*) FROM financial_metrics")).scalar() or 0
    pending_outbox = db.query(OutboxEvent).filter(OutboxEvent.status == "pending").count()

    metrics = [
        {
            "component": "postgres",
            "metric_name": "database_size_bytes",
            "metric_value": float(db_size),
            "unit": "bytes",
            "threshold": 5_000_000_000,
        },
        {
            "component": "postgres",
            "metric_name": "active_connections",
            "metric_value": float(active_connections),
            "unit": "connections",
            "threshold": float(max_connections * 0.8),
        },
        {
            "component": "timescaledb",
            "metric_name": "financial_metric_rows",
            "metric_value": float(financial_rows),
            "unit": "rows",
            "threshold": 10_000_000,
        },
        {
            "component": "outbox",
            "metric_name": "pending_events",
            "metric_value": float(pending_outbox),
            "unit": "events",
            "threshold": 1_000,
        },
    ]

    snapshots = []
    for metric in metrics:
        threshold = metric["threshold"]
        value = metric["metric_value"]
        status = "warning" if threshold and value >= threshold else "healthy"
        snapshot = CapacitySnapshot(
            **metric,
            status=status,
            details={"captured_by": "capacity_report"},
        )
        db.add(snapshot)
        snapshots.append({**metric, "status": status})
    db.commit()

    return {
        "status": "warning" if any(item["status"] == "warning" for item in snapshots) else "healthy",
        "metrics": snapshots,
    }


def partition_report(db: Session) -> dict[str, Any]:
    rows = db.execute(
        text(
            """
            SELECT h.hypertable_name, COALESCE(c.num_chunks, 0) AS num_chunks
            FROM timescaledb_information.hypertables h
            LEFT JOIN (
                SELECT hypertable_name, count(*) AS num_chunks
                FROM timescaledb_information.chunks
                GROUP BY hypertable_name
            ) c USING (hypertable_name)
            WHERE hypertable_name = 'financial_metrics'
            """
        )
    ).mappings().all()
    return {
        "strategy": "TimescaleDB hypertable partitioned by financial_metrics.period",
        "hypertables": [dict(row) for row in rows],
    }


def dependency_health(db: Session) -> dict[str, Any]:
    checks: dict[str, dict[str, Any]] = {}
    try:
        db.execute(text("SELECT 1")).scalar()
        checks["postgres"] = {"status": "ok"}
    except Exception as exc:
        checks["postgres"] = {"status": "error", "detail": str(exc)}

    try:
        redis_client().ping()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        checks["redis"] = {"status": "error", "detail": str(exc)}

    overall = "ok" if all(check["status"] == "ok" for check in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
