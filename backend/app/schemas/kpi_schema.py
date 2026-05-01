from pydantic import BaseModel

class KPISchema(BaseModel):

    name: str
    actual: float
    target: float
    status: str

    class Config:
        from_attributes = True