from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.company import Company

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/")
def get_companies(db: Session = Depends(get_db)):

    rows = db.query(Company).all()

    return [
        {
            "id": c.id,
            "name": c.name,
             "sector": c.sector,
            "revenue": c.revenue,
            "employees": c.employees,
            "ebitda": c.ebitda,
            "arr": c.arr,
        }
        for c in rows
    ]