from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.services.financial_service import generate_financial_forecast, get_financial_history
from app.services.dataset_loader import load_financial_csv, resolve_company_ids_from_csv
from app.models.financials import FinancialMetric
from app.utils.json_sanitize import sanitize_for_json
import tempfile
import os

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/{company_id}/history")
def financial_history(company_id: int, db: Session = Depends(get_db)):
    return get_financial_history(company_id, db)


@router.get("/{company_id}/forecast")
async def financial_forecast(company_id: int, db: Session = Depends(get_db)):
    return await generate_financial_forecast(company_id, db)


@router.get("/{company_id}/ml-forecast")
def ml_financial_forecast(company_id: int, target: str = "revenue", db: Session = Depends(get_db)):
    from app.ml import train_xgboost_style_forecast

    rows = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company_id)
        .order_by(FinancialMetric.period)
        .all()
    )
    payload = [
        {
            "company_id": row.company_id,
            "period": row.period,
            "revenue": row.revenue,
            "cogs": row.cogs,
            "gross_profit": row.gross_profit,
            "ebitda": row.ebitda,
        }
        for row in rows
    ]
    return train_xgboost_style_forecast(payload, company_id=company_id, target=target)


@router.post("/upload-financials")
async def upload_financial_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Save uploaded CSV
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        path = tmp.name

    try:
        # Load CSV into DB
        try:
            result = load_financial_csv(path, db)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to load CSV: {str(e)}")

        # Resolve companies and trigger orchestrator
        from app.agents.orchestrator_agent import StrategicOrchestrator

        company_ids = resolve_company_ids_from_csv(path, db)
        if not company_ids:
            raise HTTPException(status_code=400, detail="No valid company identifiers found in CSV")

        orchestrator = StrategicOrchestrator()
        results = {}
        for _, company_id in company_ids.items():
            results[str(company_id)] = await orchestrator.run_planning_cycle(company_id=company_id, db=db)

        return sanitize_for_json({
            "status": "success",
            "rows_loaded": result.rows_loaded,
            "companies_loaded": company_ids,
            "results": results,
        })
    finally:
        if os.path.exists(path):
            os.remove(path)
