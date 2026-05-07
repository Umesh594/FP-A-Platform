from sqlalchemy.orm import Session

from app.pipelines.extract import extract_seeded_financials
from app.pipelines.load import load_pipeline_run
from app.pipelines.quality_checks import run_quality_checks
from app.pipelines.transform import transform_to_warehouse


def run_beam_style_pipeline(db: Session, source_id: int | None = None) -> dict:
    raw_rows = extract_seeded_financials(db)
    checks = run_quality_checks(raw_rows)
    warehouse_payload = transform_to_warehouse(raw_rows)
    run = load_pipeline_run(db, warehouse_payload, checks, source_id=source_id)
    return {
        "id": run.id,
        "pipeline_name": run.pipeline_name,
        "status": run.status,
        "rows_extracted": run.rows_extracted,
        "rows_loaded": run.rows_loaded,
        "quality_score": run.quality_score,
        "checks": run.checks,
        "engine": "python_warehouse_pipeline",
        "note": "Use /agents/pipelines/beam/run for the real Apache Beam DirectRunner pipeline.",
    }
