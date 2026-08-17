-- Power BI semantic views for Autonomous FP&A Data Intelligence Platform.
-- These views keep dashboard calculations server-side and reproducible.

CREATE OR REPLACE VIEW powerbi_financial_fact AS
SELECT
    CAST(TO_CHAR(f.period, 'YYYYMMDD') AS INTEGER) AS date_key,
    f.period,
    TO_CHAR(f.period, 'YYYY-MM') AS month,
    c.id AS company_id,
    c.name AS company_name,
    c.sector,
    f.revenue,
    f.gross_profit,
    f.ebitda,
    CASE WHEN f.revenue = 0 THEN 0 ELSE f.gross_profit / f.revenue END AS gross_margin,
    CASE WHEN f.revenue = 0 THEN 0 ELSE f.ebitda / f.revenue END AS ebitda_margin,
    f.customer_count,
    f.price_per_customer
FROM financial_metrics f
JOIN companies c ON c.id = f.company_id;

CREATE OR REPLACE VIEW powerbi_kpi_scorecard AS
SELECT
    CAST(TO_CHAR(period, 'YYYYMMDD') AS INTEGER) AS date_key,
    company_id,
    period,
    name AS kpi_name,
    actual,
    target,
    CASE WHEN target = 0 THEN 0 ELSE actual / target END AS attainment_ratio,
    status,
    CASE WHEN status = 'At Risk' THEN 1 ELSE 0 END AS at_risk_flag
FROM kpis;

CREATE OR REPLACE VIEW powerbi_initiative_roi AS
SELECT
    i.company_id,
    c.name AS company_name,
    i.name AS initiative_name,
    i.start_date,
    i.investment,
    i.revenue_impact,
    CASE WHEN i.investment = 0 THEN 0 ELSE i.revenue_impact / i.investment END AS revenue_roi
FROM initiatives i
JOIN companies c ON c.id = i.company_id;
