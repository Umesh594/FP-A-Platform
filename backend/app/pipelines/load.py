from datetime import datetime

from sqlalchemy.orm import Session

from app.models.advanced import PipelineRun


def load_pipeline_run(db: Session, warehouse_payload: dict, checks: dict, source_id: int | None = None) -> PipelineRun:
    row = PipelineRun(
        source_id=source_id,
        pipeline_name="beam_style_financial_warehouse_pipeline",
        status="completed",
        rows_extracted=len(warehouse_payload["raw_financial_uploads"]),
        rows_loaded=len(warehouse_payload["fact_financials"]),
        quality_score=checks["quality_score"],
        checks={
            **checks,
            "warehouse_tables": {
                "raw_financial_uploads": len(warehouse_payload["raw_financial_uploads"]),
                "staging_financials": len(warehouse_payload["staging_financials"]),
                "fact_financials": len(warehouse_payload["fact_financials"]),
                "dim_company": len(warehouse_payload["dim_company"]),
                "dim_time": len(warehouse_payload["dim_time"]),
            },
        },
        completed_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
