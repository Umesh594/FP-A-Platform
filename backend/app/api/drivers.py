# app/api/drivers.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.models.driver import DriverMetric
from app.dependencies import get_db

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.get("/{company_id}")
def get_drivers(company_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(DriverMetric)
        .filter(DriverMetric.company_id == company_id)
        .order_by(DriverMetric.period)
        .all()
    )
    by_period = {}
    for row in rows:
        item = by_period.setdefault(
            row.period,
            {
                "period": row.period,
                "customer_count": None,
                "price_per_customer": None,
                "drivers": {},
            },
        )
        driver_key = (row.driver_name or "").lower()
        item["drivers"][row.driver_name] = row.value
        if driver_key in {"customer_count", "customers", "active_customers", "client_count", "clients"}:
            item["customer_count"] = row.value
        if (
            driver_key in {"price_per_customer", "asp", "average_selling_price"}
            or "average_contract_value" in driver_key
            or "price" in driver_key
        ):
            item["price_per_customer"] = row.value

    return list(by_period.values())


@router.post("/upload")
async def upload_driver_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from app.services.dataset_loader import load_driver_csv
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        path = tmp.name

    try:
        result = load_driver_csv(path, db)
        return {"status": "success", "rows_loaded": result.rows_loaded, "companies_loaded": result.company_ids}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if os.path.exists(path):
            os.remove(path)
