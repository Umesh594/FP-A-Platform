from datetime import date, datetime

from pydantic import BaseModel, Field


class WorkforcePlanCreate(BaseModel):
    company_id: int = Field(ge=1)
    department: str = Field(min_length=2, max_length=120)
    effective_month: date
    requested_headcount: int = Field(ge=0, le=100_000)
    monthly_cost_per_head: float = Field(ge=0)
    open_requisitions: int = Field(default=0, ge=0)
    business_justification: str = Field(min_length=10, max_length=2000)


class WorkforcePlanResponse(BaseModel):
    id: int
    company_id: int
    department: str
    effective_month: date
    requested_headcount: int
    monthly_cost_per_head: float
    open_requisitions: int
    status: str
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    comment: str | None = Field(default=None, max_length=1000)


class WorkdaySyncRequest(BaseModel):
    company_id: int = Field(default=1, ge=1)
