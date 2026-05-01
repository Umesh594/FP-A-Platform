from sqlalchemy.orm import Session
from app.models.kpi import KPI


def get_kpis(company_id: int, db: Session):

    rows = db.query(KPI).filter(KPI.company_id == company_id).all()

    results = []

    for k in rows:

        ratio = k.actual / k.target if k.target else 0

        if ratio >= 1:
            status = "green"
        elif ratio >= 0.9:
            status = "yellow"
        else:
            status = "red"

        results.append({
            "kpi": k.name,
            "name": k.name,
            "actual": k.actual,
            "target": k.target,
            "status": status
        })

    return results
