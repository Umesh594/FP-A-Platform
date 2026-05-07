import json
import tempfile
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.pipelines.extract import extract_seeded_financials
from app.pipelines.load import load_pipeline_run
from app.pipelines.quality_checks import run_quality_checks
from app.pipelines.transform import transform_to_warehouse


def _serialize_row(row: dict) -> dict:
    return {
        **row,
        "period": row["period"].isoformat() if row.get("period") else None,
        "revenue": float(row.get("revenue") or 0),
        "cogs": float(row.get("cogs") or 0),
        "gross_profit": float(row.get("gross_profit") or 0),
        "ebitda": float(row.get("ebitda") or 0),
    }


def _company_month_key(row: dict) -> tuple[str, dict]:
    return (f"{row['company_id']}:{row['period'][:7]}", row)


def _aggregate_financials(group: tuple[str, Iterable[dict]]) -> dict:
    key, rows = group
    grouped_rows = list(rows)
    company_id, period = key.split(":")
    revenue = sum(row["revenue"] for row in grouped_rows)
    ebitda = sum(row["ebitda"] for row in grouped_rows)
    return {
        "company_id": int(company_id),
        "period": period,
        "revenue": revenue,
        "ebitda": ebitda,
        "ebitda_margin": round(ebitda / revenue, 4) if revenue else 0,
    }


def run_apache_beam_pipeline(db: Session, source_id: int | None = None) -> dict:
    import apache_beam as beam
    from apache_beam.options.pipeline_options import PipelineOptions

    raw_rows = extract_seeded_financials(db)
    checks = run_quality_checks(raw_rows)
    warehouse_payload = transform_to_warehouse(raw_rows)
    pipeline_run = load_pipeline_run(db, warehouse_payload, checks, source_id=source_id)

    rows = [_serialize_row(row) for row in raw_rows]
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_prefix = str(Path(tmp_dir) / "beam_financials")
        options = PipelineOptions(["--runner=DirectRunner"])
        with beam.Pipeline(options=options) as pipeline:
            (
                pipeline
                | "ReadSeededFinancialRows" >> beam.Create(rows)
                | "KeyByCompanyMonth" >> beam.Map(_company_month_key)
                | "GroupFinancialRows" >> beam.GroupByKey()
                | "AggregateRevenueEbitda" >> beam.Map(_aggregate_financials)
                | "ToJson" >> beam.Map(json.dumps)
                | "WriteWarehouseFacts" >> beam.io.WriteToText(output_prefix, file_name_suffix=".jsonl", shard_name_template="")
            )

        output_file = Path(f"{output_prefix}.jsonl")
        aggregate_rows = []
        if output_file.exists():
            aggregate_rows = [json.loads(line) for line in output_file.read_text().splitlines() if line.strip()]

    return {
        "id": pipeline_run.id,
        "engine": "apache_beam",
        "runner": "DirectRunner",
        "status": "completed",
        "rows_extracted": len(rows),
        "rows_loaded": len(aggregate_rows),
        "quality_score": checks["quality_score"],
        "sample_output": aggregate_rows[:5],
        "warehouse_tables": pipeline_run.checks.get("warehouse_tables", {}),
    }
