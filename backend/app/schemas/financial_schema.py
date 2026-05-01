from pydantic import BaseModel, Field
from typing import List
from datetime import date

class FinancialMetricSchema(BaseModel):
    company_id: int
    period: date
    revenue: float = Field(default=0)
    cogs: float = Field(default=0)
    gross_profit: float = Field(default=0)
    ebitda: float = Field(default=0)
    customer_count: float = Field(default=0)
    price_per_customer: float = Field(default=0)

    model_config = {
        "from_attributes": True  # works with ORM objects
    }


class FinancialForecastSchema(BaseModel):
    revenue_forecast: List[float] = Field(default_factory=list)
    expense_forecast: List[float] = Field(default_factory=list)
    capital_analysis: List[float] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }