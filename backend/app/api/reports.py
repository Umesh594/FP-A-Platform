from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse, StreamingResponse
from app.dependencies import get_db
from app.agents.reporting_agent import ReportingAgent
from app.models.company import Company
from app.models.financials import FinancialMetric
from app.models.initiative import Initiative
from app.models.kpi import KPI
import os
import uuid
import csv
import io

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/board-pack")
async def generate_board_pack(db: Session = Depends(get_db)):
    try:
        reporting_agent = ReportingAgent()

        # ✅ Agent handles EVERYTHING (DB → insights → PDF)
        file_path = reporting_agent.generate_board_pack(
            filename=f"board_pack_{uuid.uuid4()}.pdf",
            db=db
        )

        # ✅ Safety check
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="PDF generation failed")

        # ✅ Directly return file (NO DB storage)
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename="board_pack.pdf"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/board-pack/preview")
def board_pack_preview(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.id).all()
    total_revenue = sum(c.revenue or 0 for c in companies)
    total_ebitda = sum(c.ebitda or 0 for c in companies)
    return {
        "title": "Monthly Board Pack",
        "companies": len(companies),
        "total_revenue": total_revenue,
        "total_ebitda": total_ebitda,
        "ebitda_margin": (total_ebitda / total_revenue) if total_revenue else 0,
        "sections": [
            "Executive Summary",
            "Consolidated Financials",
            "KPI Scorecard",
            "Variance Commentary",
            "Strategic Initiatives",
            "Scenario Analysis",
        ],
    }


def csv_response(filename: str, headers: list[str], rows: list[list[object]]):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/{export_type}")
def export_data(export_type: str, db: Session = Depends(get_db)):
    if export_type == "companies":
        rows = db.query(Company).order_by(Company.id).all()
        return csv_response(
            "portfolio_companies.csv",
            ["id", "name", "sector", "revenue", "ebitda", "arr", "employees"],
            [[r.id, r.name, r.sector, r.revenue, r.ebitda, r.arr, r.employees] for r in rows],
        )
    if export_type == "financials":
        rows = db.query(FinancialMetric).order_by(FinancialMetric.company_id, FinancialMetric.period).all()
        return csv_response(
            "financial_metrics.csv",
            ["company_id", "period", "revenue", "cogs", "gross_profit", "ebitda"],
            [[r.company_id, r.period, r.revenue, r.cogs, r.gross_profit, r.ebitda] for r in rows],
        )
    if export_type == "kpis":
        rows = db.query(KPI).order_by(KPI.company_id, KPI.period, KPI.name).all()
        return csv_response(
            "kpis.csv",
            ["company_id", "period", "name", "actual", "target", "status"],
            [[r.company_id, r.period, r.name, r.actual, r.target, r.status] for r in rows],
        )
    if export_type == "initiatives":
        rows = db.query(Initiative).order_by(Initiative.company_id, Initiative.id).all()
        return csv_response(
            "initiatives.csv",
            ["company_id", "name", "description", "investment", "revenue_impact", "start_date"],
            [[r.company_id, r.name, r.description, r.investment, r.revenue_impact, r.start_date] for r in rows],
        )
    raise HTTPException(status_code=404, detail="Unknown export type")


@router.get("/dataroom/files")
def data_room_files(db: Session = Depends(get_db)):
    return [
        {"id": "companies", "name": "Portfolio Companies.csv", "category": "Portfolio", "size": "live", "uploaded": "seeded", "export_type": "companies"},
        {"id": "financials", "name": "Historical Financial Metrics.csv", "category": "Financials", "size": "live", "uploaded": "seeded", "export_type": "financials"},
        {"id": "kpis", "name": "KPI History.csv", "category": "KPI Reports", "size": "live", "uploaded": "seeded", "export_type": "kpis"},
        {"id": "initiatives", "name": "Strategic Initiatives.csv", "category": "Initiatives", "size": "live", "uploaded": "seeded", "export_type": "initiatives"},
    ]
