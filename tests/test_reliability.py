import os
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.advanced import IdempotencyRecord
from app.services.reliability import canonical_hash, run_idempotent


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine, tables=[IdempotencyRecord.__table__])
    return sessionmaker(bind=engine)()


def test_canonical_hash_is_order_independent():
    left = {"company_id": 1, "request_type": "planning_cycle"}
    right = {"request_type": "planning_cycle", "company_id": 1}

    assert canonical_hash(left) == canonical_hash(right)


def test_run_idempotent_replays_completed_response():
    db = make_session()
    calls = {"count": 0}

    def operation():
        calls["count"] += 1
        return {"job_id": 42, "created_at": datetime(2026, 1, 1)}

    first = run_idempotent(
        db,
        endpoint="/platform/planning-jobs",
        idempotency_key="job-1",
        request_payload={"company_id": 1},
        operation=operation,
    )
    second = run_idempotent(
        db,
        endpoint="/platform/planning-jobs",
        idempotency_key="job-1",
        request_payload={"company_id": 1},
        operation=operation,
    )

    assert first["status"] == "created"
    assert second["status"] == "replayed"
    assert second["response"]["job_id"] == 42
    assert calls["count"] == 1


def test_run_idempotent_rejects_key_reuse_with_different_payload():
    db = make_session()

    run_idempotent(
        db,
        endpoint="/platform/planning-jobs",
        idempotency_key="job-1",
        request_payload={"company_id": 1},
        operation=lambda: {"job_id": 1},
    )
    conflict = run_idempotent(
        db,
        endpoint="/platform/planning-jobs",
        idempotency_key="job-1",
        request_payload={"company_id": 2},
        operation=lambda: {"job_id": 2},
    )

    assert conflict["status"] == "conflict"
