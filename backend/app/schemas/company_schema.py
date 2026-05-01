from pydantic import BaseModel
class CompanySchema(BaseModel):

    id: int
    name: str
    sector: str
    revenue: float
    ebitda: float
    arr: float

    class Config:
        from_attributes = True