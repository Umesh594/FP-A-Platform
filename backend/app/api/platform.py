from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.reliability import (
    database_capacity_report,
    dependency_health,
    drain_outbox,
    enqueue_outbox_event,
    partition_report,
    run_idempotent,
)

router = APIRouter(prefix="/platform", tags=["platform-reliability"])


class PlanningJobRequest(BaseModel):
    company_id: int = Field(default=1, ge=1)
    notify_email: str | None = None
    request_type: str = "planning_cycle"


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    health = dependency_health(db)
    if health["status"] != "ok":
        raise HTTPException(status_code=503, detail=health)
    return health


@router.get("/capacity")
def capacity(db: Session = Depends(get_db)):
    return database_capacity_report(db)


@router.get("/partitions")
def partitions(db: Session = Depends(get_db)):
    return partition_report(db)


@router.post("/outbox/drain")
def outbox_drain(batch_size: int = 10, db: Session = Depends(get_db)):
    return drain_outbox(db, batch_size=batch_size)


@router.post("/planning-jobs")
def create_planning_job(
    payload: PlanningJobRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    request_payload = payload.model_dump()

    def operation():
        event = enqueue_outbox_event(
            db,
            aggregate_type="company",
            aggregate_id=str(payload.company_id),
            event_type="planning_cycle.requested",
            payload=request_payload,
        )

        try:
            from app.tasks.celery_app import run_planning_cycle_task

            task = run_planning_cycle_task.delay(payload.company_id, payload.notify_email)
            task_id = task.id
        except Exception as exc:
            task_id = None
            event.last_error = f"Celery enqueue failed; outbox retained for retry: {exc}"
            db.commit()

        return {
            "job_id": event.id,
            "task_id": task_id,
            "company_id": payload.company_id,
            "status": "queued",
            "delivery": "celery_with_outbox_fallback",
        }

    result = run_idempotent(
        db,
        endpoint="/platform/planning-jobs",
        idempotency_key=idempotency_key,
        request_payload=request_payload,
        operation=operation,
    )

    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["message"])
    return result
