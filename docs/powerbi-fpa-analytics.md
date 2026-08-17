# Power BI FP&A Analytics Layer

This project now exposes a production-style BI layer for Power BI reporting and financial decision analysis.

## Refresh Options

1. API mode: connect Power BI Web connector to `/powerbi/executive-dataset` and `/powerbi/data-quality-scorecard`.
2. Warehouse mode: apply `backend/sql/powerbi_semantic_views.sql` and import `powerbi_financial_fact`, `powerbi_kpi_scorecard`, and `powerbi_initiative_roi`.

## Report Pages

1. CFO overview: revenue, EBITDA, gross margin, EBITDA margin, MoM growth, at-risk KPI count.
2. Portfolio performance: sector/company ranking, revenue per customer, margin trend.
3. KPI scorecard: target attainment, at-risk KPIs, company-level drillthrough.
4. Initiative ROI: investment vs revenue impact, ROI ranking, start-date trend.
5. Model governance: forecast accuracy, drift breach count, retrain-readiness status.

## Business Value

The BI layer turns operational FP&A records into executive metrics. It gives finance teams refreshable Power BI datasets, consistent DAX measures, API-level data quality scoring, and warehouse views that prevent dashboard teams from recreating KPI logic manually.
