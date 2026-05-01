from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.kpi_service import get_kpis

router = APIRouter(prefix="/kpis", tags=["kpis"])


@router.get("/")
def all_kpis(db: Session = Depends(get_db)):
    results = []
    for company_id in range(1, 7):
        for row in get_kpis(company_id, db):
            row["company_id"] = company_id
            results.append(row)
    return results


@router.get("/{company_id}")
def company_kpis(company_id: int, db: Session = Depends(get_db)):

    return get_kpis(company_id, db)
