from pydantic import BaseModel

class ForecastSchema(BaseModel):

    month: str
    revenue: float
    ebitda: float