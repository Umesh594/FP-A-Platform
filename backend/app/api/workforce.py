from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.workforce import WorkforceApproval, WorkforcePlan
from app.schemas.workforce import ApprovalDecision, WorkdaySyncRequest, WorkforcePlanCreate, WorkforcePlanResponse
from app.security import get_current_user
from app.services.privacy import stable_hash
from app.services.reliability import run_idempotent
from app.services.workforce_service import sync_workday_actuals, transition_plan, workforce_dataset

router = APIRouter(prefix="/workforce", tags=["employee-success-workforce-planning"])


@router.post("/plans", response_model=dict)
def create_plan(
    payload: WorkforcePlanCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    def operation():
        plan = WorkforcePlan(**payload.model_dump(), requester_id_hash=stable_hash(user["user_id"]))
        db.add(plan)
        db.flush()
        return {"plan_id": plan.id, "status": plan.status, "monthly_planned_cost": round(plan.requested_headcount * plan.monthly_cost_per_head, 2)}

    result = run_idempotent(db, endpoint="/workforce/plans", idempotency_key=idempotency_key, request_payload=payload.model_dump(mode="json"), operation=operation)
    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["message"])
    return result


@router.get("/plans", response_model=list[WorkforcePlanResponse])
def list_plans(company_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(WorkforcePlan).order_by(WorkforcePlan.effective_month.desc(), WorkforcePlan.department)
    if company_id is not None:
        query = query.filter(WorkforcePlan.company_id == company_id)
    return query.all()


@router.post("/plans/{plan_id}/submit", response_model=WorkforcePlanResponse)
def submit_plan(plan_id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.get(WorkforcePlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Workforce plan not found")
    try:
        transition_plan(db, plan, "submitted", user["user_id"])
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.refresh(plan)
    return plan


@router.post("/plans/{plan_id}/decision", response_model=WorkforcePlanResponse)
def decide_plan(plan_id: int, payload: ApprovalDecision, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user["role"] not in {"CFO", "Admin", "HR Approver"}:
        raise HTTPException(status_code=403, detail="Approval permission is required")
    plan = db.get(WorkforcePlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Workforce plan not found")
    try:
        transition_plan(db, plan, payload.decision, user["user_id"], payload.comment)
        db.add(WorkforceApproval(plan_id=plan.id, decision=payload.decision, approver_id_hash=stable_hash(user["user_id"]), comment=payload.comment))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.refresh(plan)
    return plan


@router.post("/workday/sync")
def sync_workday(payload: WorkdaySyncRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), db: Session = Depends(get_db)):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    result = run_idempotent(db, endpoint="/workforce/workday/sync", idempotency_key=idempotency_key, request_payload=payload.model_dump(), operation=lambda: sync_workday_actuals(db, payload.company_id))
    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["message"])
    return result


@router.get("/analytics/dataset")
def workforce_analytics(company_id: int | None = None, db: Session = Depends(get_db)):
    return workforce_dataset(db, company_id)
