# Financial Warehouse Pipelines

This project includes three pipeline execution modes:

- `python_warehouse_pipeline`: lightweight in-process ETL/ELT pipeline for Render-safe API execution.
- `apache_beam`: real Apache Beam DirectRunner pipeline exposed at `POST /agents/pipelines/beam/run`.
- `apache_spark`: real PySpark local pipeline exposed at `POST /agents/pipelines/spark/run`.

The warehouse model includes raw, staging, fact, and dimension tables:

- `raw_financial_uploads`
- `staging_financials`
- `fact_financials`
- `dim_company`
- `dim_time`
- `dim_department`
- `dim_kpi`
- `forecast_results`
- `scenario_results`

Optional local Spark infrastructure:

```powershell
docker compose --profile analytics up -d spark-master spark-worker
```

Spark UI:

```text
http://localhost:8081
```
