import os
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.connectors.workday_connector import WorkdayConfig, WorkdayWorkforceConnector
from app.models.advanced import OutboxEvent
from app.models.workforce import WorkforceActual, WorkforceApproval, WorkforcePlan
from app.services.workforce_service import sync_workday_actuals, transition_plan, workforce_dataset


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        bind=engine,
        tables=[WorkforcePlan.__table__, WorkforceApproval.__table__, WorkforceActual.__table__, OutboxEvent.__table__],
    )
    return sessionmaker(bind=engine)()


def test_workday_mock_feed_has_four_valid_department_months():
    connector = WorkdayWorkforceConnector(config=WorkdayConfig("", "", mock_mode=True))
    rows = connector.fetch_department_months()

    assert len(rows) == 4
    assert {row["department"] for row in rows} == {"Engineering", "Sales", "People", "Finance"}
    assert all(row["actual_headcount"] >= 0 for row in rows)


def test_workforce_approval_emits_salesforce_event_contract():
    db = make_session()
    plan = WorkforcePlan(
        company_id=1,
        department="Engineering",
        effective_month=date(2026, 11, 1),
        requested_headcount=3,
        monthly_cost_per_head=12000,
        requester_id_hash="requester",
        business_justification="Capacity required for the approved roadmap.",
    )
    db.add(plan)
    db.commit()

    transition_plan(db, plan, "submitted", "planner-1")
    transition_plan(db, plan, "approved", "approver-1", "Approved for the next planning cycle")

    event = db.query(OutboxEvent).filter_by(event_type="workforce.plan.approved").one()
    assert plan.status == "approved"
    assert event.payload["event_contract"] == "Salesforce Workforce_Plan_Approved__e"
    assert event.payload["monthly_planned_cost"] == 36000


def test_workday_sync_and_dataset_calculate_planned_variance():
    db = make_session()
    result = sync_workday_actuals(db, 1, WorkdayWorkforceConnector(config=WorkdayConfig("", "", mock_mode=True)))
    plan = WorkforcePlan(
        company_id=1,
        department="Engineering",
        effective_month=date(2026, 11, 1),
        requested_headcount=40,
        monthly_cost_per_head=12000,
        status="approved",
        requester_id_hash="requester",
        business_justification="Approved engineering capacity plan for the next planning cycle.",
    )
    db.add(plan)
    db.commit()

    engineering = next(row for row in workforce_dataset(db, 1) if row["department"] == "Engineering")
    assert result["rows_received"] == 4
    assert engineering["headcount_variance"] == 2
    assert engineering["cost_variance"] == 24000
