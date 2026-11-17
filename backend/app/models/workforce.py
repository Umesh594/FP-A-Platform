from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from app.database import Base


class WorkforcePlan(Base):
    """A department-month headcount request; no direct employee PII is stored."""

    __tablename__ = "workforce_plans"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    effective_month = Column(Date, index=True, nullable=False)
    requested_headcount = Column(Integer, nullable=False)
    monthly_cost_per_head = Column(Float, nullable=False)
    open_requisitions = Column(Integer, default=0, nullable=False)
    status = Column(String, default="draft", index=True, nullable=False)
    requester_id_hash = Column(String, nullable=False)
    business_justification = Column(Text, nullable=False)
    source = Column(String, default="manual", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "department", "effective_month", "source", name="uq_workforce_plan_period_source"),
    )


class WorkforceApproval(Base):
    __tablename__ = "workforce_approvals"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("workforce_plans.id"), index=True, nullable=False)
    decision = Column(String, nullable=False)
    approver_id_hash = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkforceActual(Base):
    """Monthly aggregated Workday/HRIS data kept at department grain for planning."""

    __tablename__ = "workforce_actuals"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    department = Column(String, index=True, nullable=False)
    period = Column(Date, index=True, nullable=False)
    actual_headcount = Column(Integer, nullable=False)
    actual_monthly_cost = Column(Float, nullable=False)
    source = Column(String, default="workday", nullable=False)
    quality_status = Column(String, default="valid", nullable=False)
    synced_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "department", "period", "source", name="uq_workforce_actual_period_source"),
    )
