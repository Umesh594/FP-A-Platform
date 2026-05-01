from pydantic import BaseModel
from typing import Optional
from datetime import date

class InitiativeCreate(BaseModel):
    company_id: int
    description: Optional[str]
    name: str
    investment: float
    revenue_impact: float


class InitiativeUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    investment: Optional[float]
    revenue_impact: Optional[float]


class InitiativeResponse(BaseModel):
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    investment: float
    revenue_impact: float
    start_date: Optional[date] = None

    class Config:
        from_attributes = True