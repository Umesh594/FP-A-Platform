from sqlalchemy.orm import Session

from app.pipelines.extract import extract_seeded_financials
from app.pipelines.load import load_pipeline_run
from app.pipelines.quality_checks import run_quality_checks
from app.pipelines.transform import transform_to_warehouse


def run_spark_pipeline(db: Session, source_id: int | None = None) -> dict:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    raw_rows = extract_seeded_financials(db)
    checks = run_quality_checks(raw_rows)
    warehouse_payload = transform_to_warehouse(raw_rows)
    pipeline_run = load_pipeline_run(db, warehouse_payload, checks, source_id=source_id)

    rows = [
        {
            "company_id": int(row["company_id"]),
            "period": row["period"].isoformat() if row.get("period") else None,
            "revenue": float(row.get("revenue") or 0),
            "cogs": float(row.get("cogs") or 0),
            "gross_profit": float(row.get("gross_profit") or 0),
            "ebitda": float(row.get("ebitda") or 0),
        }
        for row in raw_rows
    ]

    spark = (
        SparkSession.builder.appName("AutonomousFPAWarehousePipeline")
        .master("local[*]")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    try:
        df = spark.createDataFrame(rows)
        fact_df = (
            df.withColumn("period_month", F.substring("period", 1, 7))
            .groupBy("company_id", "period_month")
            .agg(
                F.sum("revenue").alias("revenue"),
                F.sum("cogs").alias("cogs"),
                F.sum("gross_profit").alias("gross_profit"),
                F.sum("ebitda").alias("ebitda"),
            )
            .withColumn("ebitda_margin", F.when(F.col("revenue") != 0, F.col("ebitda") / F.col("revenue")).otherwise(F.lit(0)))
            .orderBy("company_id", "period_month")
        )
        sample = [row.asDict() for row in fact_df.limit(5).collect()]
        rows_loaded = fact_df.count()
    finally:
        spark.stop()

    return {
        "id": pipeline_run.id,
        "engine": "apache_spark",
        "master": "local[*]",
        "status": "completed",
        "rows_extracted": len(rows),
        "rows_loaded": rows_loaded,
        "quality_score": checks["quality_score"],
        "sample_output": sample,
        "warehouse_tables": pipeline_run.checks.get("warehouse_tables", {}),
    }
