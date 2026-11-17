from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.connectors.workday_connector import WorkdayWorkforceConnector
from app.models.workforce import WorkforceActual, WorkforcePlan
from app.services.privacy import audit_event, stable_hash
from app.services.reliability import enqueue_outbox_event


VALID_TRANSITIONS = {"draft": {"submitted"}, "submitted": {"approved", "rejected"}}


def transition_plan(db: Session, plan: WorkforcePlan, target_status: str, actor_id: str, comment: str | None = None) -> WorkforcePlan:
    if target_status not in VALID_TRANSITIONS.get(plan.status, set()):
        raise ValueError(f"Cannot transition workforce plan from {plan.status} to {target_status}")
    previous_status = plan.status
    plan.status = target_status
    db.flush()
    enqueue_outbox_event(
        db,
        aggregate_type="workforce_plan",
        aggregate_id=str(plan.id),
        event_type=f"workforce.plan.{target_status}",
        payload={
            "plan_id": plan.id,
            "company_id": plan.company_id,
            "department": plan.department,
            "effective_month": plan.effective_month.isoformat(),
            "requested_headcount": plan.requested_headcount,
            "monthly_planned_cost": round(plan.requested_headcount * plan.monthly_cost_per_head, 2),
            "previous_status": previous_status,
            "actor_id_hash": stable_hash(actor_id),
            "comment_present": bool(comment),
            "event_contract": "Salesforce Workforce_Plan_Approved__e" if target_status == "approved" else None,
        },
    )
    audit_event("workforce_plan_transition", plan_id=plan.id, from_status=previous_status, to_status=target_status, actor_id=actor_id)
    return plan


def sync_workday_actuals(db: Session, company_id: int, connector: WorkdayWorkforceConnector | None = None) -> dict:
    rows = (connector or WorkdayWorkforceConnector()).fetch_department_months()
    inserted = 0
    updated = 0
    for row in rows:
        actual = db.query(WorkforceActual).filter_by(
            company_id=company_id, department=row["department"], period=row["period"], source="workday"
        ).one_or_none()
        if actual is None:
            db.add(WorkforceActual(company_id=company_id, **row))
            inserted += 1
        else:
            actual.actual_headcount = row["actual_headcount"]
            actual.actual_monthly_cost = row["actual_monthly_cost"]
            actual.quality_status = row["quality_status"]
            actual.synced_at = datetime.utcnow()
            updated += 1
    db.flush()
    event = enqueue_outbox_event(
        db,
        aggregate_type="workforce_actuals",
        aggregate_id=str(company_id),
        event_type="workday.workforce.synced",
        payload={"company_id": company_id, "rows_received": len(rows), "rows_inserted": inserted, "rows_updated": updated},
    )
    audit_event("workday_workforce_synced", company_id=company_id, rows_received=len(rows), rows_inserted=inserted, rows_updated=updated)
    return {"rows_received": len(rows), "rows_inserted": inserted, "rows_updated": updated, "sync_event_id": event.id}


def workforce_dataset(db: Session, company_id: int | None = None) -> list[dict]:
    actuals = db.query(WorkforceActual)
    plans = db.query(WorkforcePlan).filter(WorkforcePlan.status == "approved")
    if company_id is not None:
        actuals = actuals.filter(WorkforceActual.company_id == company_id)
        plans = plans.filter(WorkforcePlan.company_id == company_id)
    approved_by_key = {(p.company_id, p.department, p.effective_month): p for p in plans.all()}
    rows = []
    for actual in actuals.order_by(WorkforceActual.period, WorkforceActual.department).all():
        plan = approved_by_key.get((actual.company_id, actual.department, actual.period))
        planned_headcount = plan.requested_headcount if plan else actual.actual_headcount
        planned_cost = plan.requested_headcount * plan.monthly_cost_per_head if plan else actual.actual_monthly_cost
        rows.append({
            "company_id": actual.company_id,
            "department": actual.department,
            "period": actual.period.isoformat(),
            "actual_headcount": actual.actual_headcount,
            "planned_headcount": planned_headcount,
            "headcount_variance": actual.actual_headcount - planned_headcount,
            "actual_monthly_cost": round(actual.actual_monthly_cost, 2),
            "planned_monthly_cost": round(planned_cost, 2),
            "cost_variance": round(actual.actual_monthly_cost - planned_cost, 2),
            "open_requisitions": plan.open_requisitions if plan else 0,
            "data_quality_status": actual.quality_status,
        })
    return rows
