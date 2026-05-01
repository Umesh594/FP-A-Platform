from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.agents.orchestrator_agent import StrategicOrchestrator
from app.dependencies import get_db
from app.services.financial_service import generate_financial_forecast, get_financial_history
from app.services.dataset_loader import load_financial_csv, resolve_company_ids_from_csv
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
