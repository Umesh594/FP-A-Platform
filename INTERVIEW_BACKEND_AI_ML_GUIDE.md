# Interview Guide: Backend, AI/ML, Agents, APIs

This project is an Autonomous FP&A Platform. FP&A means Financial Planning and Analysis. The application helps finance teams load company financial data, forecast revenue and expenses, monitor KPIs, run scenarios, detect anomalies, create recommendations, and generate board-ready reports.

In an interview, explain it like this:

> I built a full-stack finance planning system with a FastAPI backend, React frontend, PostgreSQL/TimescaleDB storage, ML forecasting, anomaly detection, Monte Carlo scenarios, LLM-assisted variance explanations, agent orchestration, RBAC-secured tools, enterprise connectors, data pipelines, reporting, and observability.

## 1. High-Level Architecture

The project has these layers:

1. Frontend: React + Vite + TypeScript.
   - Main pages: portfolio dashboard, company detail, scenario builder, KPI scorecard, reports/exports, email center, agent intelligence, admin/RBAC.
   - API client calls backend endpoints such as `/financials`, `/agents`, `/scenarios`, `/reports`.

2. Backend API: FastAPI.
   - Entry point: `backend/app/main.py`.
   - Registers routers for companies, financials, KPIs, reports, initiatives, variances, drivers, emails, orchestrator, portfolio, agents, auth, platform, integrations, and PowerBI.
   - Adds CORS.
   - Adds API key middleware, request IDs, latency headers, and audit logging.

3. Database: SQLAlchemy with PostgreSQL.
   - `database.py` creates the engine and sessions.
   - `init_database()` creates tables and tries to enable TimescaleDB hypertable support for time-series financial data.

4. ML layer:
   - Main file: `backend/app/ml/forecasting_service.py`.
   - Uses XGBoost if installed, otherwise sklearn GradientBoostingRegressor.
   - Uses lag features, rolling features, seasonality features, walk-forward validation, prediction intervals, anomaly detection, and monitoring.

5. Agent layer:
   - Main files: `backend/app/agents/*.py` and `backend/app/services/agentic_system.py`.
   - Agents include revenue, expense, KPI, variance, scenario, budget, capital planning, reporting, initiative, and orchestrator agents.
   - Some agents are deterministic finance logic. Variance explanation can call Groq Llama if a Groq API key is configured.

6. Enterprise/platform layer:
   - Connectors: CSV, PostgreSQL, S3, Google Sheets, mock ERP, Salesforce, Oracle.
   - Pipelines: extract, transform, quality checks, load, Beam-style, real Apache Beam, Spark.
   - Reliability: idempotency, locks, outbox events, capacity and dependency health.
   - Security: demo auth, roles, RBAC, tool audit logs, API key middleware.

## 2. `main.py`: Backend Entry Point

Important methods and logic:

### `app = FastAPI(...)`

Creates the web server with the title `Autonomous FP&A Platform`.

### `api_key_middleware(request, call_next)`

What it does:
- Reads or creates an `X-Request-ID`.
- Measures request latency.
- If `settings.API_KEY` exists, every request must send matching `X-API-Key`, except `/docs` and `/openapi.json`.
- Rejected requests are logged through `audit_event`.
- Successful responses get:
  - `X-Request-ID`
  - `X-Response-Time-Ms`

Why this is good:
- It gives basic API protection for demo/enterprise deployment.
- Request IDs help debugging.
- Latency headers support observability.
- Audit logging helps compliance.

### `app.add_middleware(CORSMiddleware, ...)`

Allows the frontend to call the backend. In production, `allow_origins=["*"]` should be restricted to real frontend domains.

### `include_router(...)`

Registers all feature modules. This keeps code modular instead of putting every endpoint into one giant file.

### `/health`

Simple health check returning backend status.

### `startup()`

Initializes database tables and optionally starts the scheduler.

## 3. Database and Models

### `config.py`

Uses `pydantic_settings.BaseSettings` to load environment variables:
- `DATABASE_URL`
- `REDIS_URL`
- `GROQ_API_KEY`
- `SENDGRID_API_KEY`
- Salesforce/Oracle credentials
- API key
- scheduler settings
- mock mode flags

Why:
- Secrets and environment-specific settings should not be hardcoded.
- Mock mode allows interview/demo execution without real Salesforce or Oracle credentials.

### `database.py`

Key parts:
- `create_engine(settings.DATABASE_URL, pool_pre_ping=True)`: creates DB connection pool and checks stale connections.
- `SessionLocal`: creates per-request SQLAlchemy sessions.
- `Base = declarative_base()`: base class for models.
- `init_timescaledb()`: tries to enable TimescaleDB and convert `financial_metrics` into a hypertable on `period`.
- `init_database()`: creates tables under a PostgreSQL advisory lock.

Why advisory lock:
- If multiple app instances start together, only one creates/migrates tables at a time.

### `FinancialMetric`

Composite primary key:
- `company_id`
- `period`

Fields:
- `revenue`
- `cogs`
- `gross_profit`
- `ebitda`
- `customer_count`
- `price_per_customer`

Why:
- Financials are time-series data per company.
- Composite key prevents duplicate monthly records for same company.
- Driver fields support driver-based revenue forecasting.

### Advanced models

Important tables:
- `AgentRun`: one planning cycle execution.
- `AgentTrace`: every agent step, tool call, thought, output, latency, tokens, estimated cost.
- `AgentReflection`: self-review output.
- `EvalRun`: evaluation metrics.
- `Recommendation`: generated business recommendation.
- `DataSource`: configured external systems.
- `PipelineRun`: ETL pipeline result.
- `ToolAuditLog`: RBAC tool execution audit.
- `ForecastExperiment`: model training metadata.
- `ForecastPoint`: future forecast rows.
- `AnomalyFlag`: anomaly detection output.
- `ModelMonitoringSnapshot`: drift/retrain monitoring.
- `IdempotencyRecord`, `OutboxEvent`, `CapacitySnapshot`: reliability and production readiness.

## 4. Main ML Forecasting: `forecasting_service.py`

This is the most important AI/ML file.

### Supported targets

`SUPPORTED_TARGETS = {"revenue", "expense", "cash_flow", "ebitda", "gross_profit", "cogs"}`

Meaning:
- The same pipeline can forecast different financial targets.
- Expense and cash flow are derived when not directly stored.

### Feature columns

The model uses:
- Calendar: `month`, `quarter`, `year`
- Date flags: `is_month_end`, `is_quarter_end`
- Seasonality: `sin_month`, `cos_month`
- Trend: `trend_index`
- Lags: `lag_1`, `lag_7`, `lag_30`
- Rolling stats: rolling mean/std for 3, 6, 12 periods
- Decomposition: smoothed trend and monthly seasonal effect

Interview explanation:

> I converted raw financial history into supervised learning rows. Because time-series models need past behavior as input, I added lag features, rolling averages, volatility features, trend index, and cyclical month encodings. This lets tree-based models learn seasonality, momentum, and recent financial patterns.

### `mape(actual, predicted)`

Calculates Mean Absolute Percentage Error.

Formula:
- `abs(actual - predicted) / actual`
- Average across all non-zero actual values.

Why mask zeros:
- Division by zero would break metric calculation.

Use in interview:

> MAPE is easy for finance users because it says the forecast error as a percentage, for example 6 percent error.

### `_metrics(actual, predicted)`

Returns:
- `mae`: average absolute dollar error.
- `rmse`: penalizes large errors more.
- `mape`: percentage error.

Why three metrics:
- MAE is interpretable.
- RMSE catches big misses.
- MAPE is business-friendly.

### `_target_value(row, target)`

This converts one database row into the target value:
- For `expense`: `cogs + operating_expense`
  - operating expense is `gross_profit - ebitda`
- For `cash_flow`: `ebitda - 8 percent of cogs`
- Otherwise direct column value.

Why:
- The database stores core financial metrics, but not every derived planning target.
- Derived targets allow reusable forecasting.

### `build_feature_frame(rows, target)`

This is feature engineering.

Step by step:
1. Validate target.
2. Convert list of dicts into DataFrame.
3. Convert `period` to datetime.
4. Sort by period.
5. Drop duplicate periods, keeping latest.
6. Create `y`, the target value.
7. Extract month, quarter, year.
8. Add month-end and quarter-end flags.
9. Add sine/cosine month encoding.
10. Add trend index from 0 to N.
11. Add lag values from prior periods.
12. Add rolling mean and rolling standard deviation.
13. Add simple decomposition trend using centered rolling average.
14. Add seasonal effect as monthly average minus global average.
15. Replace infinities/NaNs and forward/backfill.

Why sine/cosine:
- Month 12 and month 1 are close in real life, but raw numbers make them far apart.
- Sine/cosine preserves cyclical seasonality.

Why lag features:
- Financial performance usually depends on recent history.

Why rolling features:
- Rolling mean captures recent level.
- Rolling std captures volatility/risk.

### `_new_regressor()`

Chooses model:
- If XGBoost is installed: `XGBRegressor`.
- Else: `GradientBoostingRegressor`.

XGBoost settings:
- `n_estimators=140`: number of boosted trees.
- `max_depth=3`: shallow trees reduce overfitting.
- `learning_rate=0.05`: small learning rate for stable learning.
- `subsample=0.9`, `colsample_bytree=0.9`: randomness improves generalization.
- `objective="reg:squarederror"`: regression loss.
- `random_state=42`: reproducibility.

Why this choice:

> XGBoost is strong for tabular finance data because it handles nonlinear relationships, lag features, seasonality, and interactions without requiring huge datasets. I added sklearn Gradient Boosting as a fallback so local tests still run if XGBoost is unavailable.

### `_baseline_prediction(train, test_periods)`

Compares ML model against a baseline.

If `ENABLE_PROPHET_BASELINE=true` and Prophet is available:
- Fit Prophet on historical data.
- Predict test periods.

Otherwise:
- Seasonal naive baseline: use same period last year if available.
- If not available, repeat last observed value.

Why baseline:
- An ML model is only useful if it beats a simple method.
- This proves the champion model is better than naive forecasting.

### `walk_forward_validate(df)`

This is time-series validation.

How it works:
1. Pick a minimum training size.
2. For each future point:
   - Train model on all data before that point.
   - Predict the next point.
   - Also predict with baseline.
   - Store actual, prediction, baseline prediction, and error.
3. Return model metrics and baseline metrics.

Why walk-forward:
- Random train/test split is wrong for time-series because it leaks future information.
- Walk-forward simulates real forecasting: train on the past, predict the future.

Interview sentence:

> I used walk-forward validation because in finance forecasting we must respect time order. Each fold only trains on historical periods and predicts the next unseen period.

### `_future_periods(last_period, horizon)`

Creates future monthly periods starting from next month.

### `forecast_future(df, horizon, validation)`

Creates final future forecasts.

Steps:
1. Train champion model on full history.
2. Calculate residuals from validation.
3. Build prediction interval:
   - `1.96 * std(residuals)` if residuals exist.
   - otherwise 5 percent of average target.
4. For each future month:
   - Build features using history plus prior predictions.
   - Predict next value.
   - Clamp negative predictions to zero.
   - Store prediction, lower bound, upper bound.
   - Add prediction back to history so later months use earlier predictions.

Why recursive forecasting:
- For multi-month forecasts, future lag values are not known.
- So the model feeds its own previous predictions into later feature rows.

### `detect_anomalies(df, validation, contamination=0.08)`

Combines two anomaly methods:

1. Rolling z-score:
   - Compares actual value to rolling mean.
   - Divides by rolling standard deviation.
   - Good for sudden unusual jumps/drops.

2. Isolation Forest:
   - Unsupervised anomaly detection.
   - Learns which rows look isolated in feature space.
   - Uses target, lags, rolling stats, and seasonality.

The final score is:
- max(abs(z-score), isolation forest decision score)

Then:
- threshold is max of 2.5 and 92nd percentile.
- high severity if score >= 3.5.

Why combine methods:
- Z-score is simple and explainable.
- Isolation Forest catches multivariate anomalies.
- Combining gives both interpretability and stronger detection.

### `monitoring_snapshot(validation, threshold_mape)`

Looks at recent validation folds and calculates rolling MAE/RMSE/MAPE.

If rolling MAPE exceeds threshold:
- `retrain_recommended=True`
- `drift_status="retrain"`

Why:
- Model performance can degrade as business conditions change.
- This is model monitoring / drift detection.

### `_log_mlflow(payload, params)`

If MLflow is installed:
- Creates experiment `autonomous-fpa-forecasting`.
- Logs params.
- Logs champion and baseline metrics.
- Returns MLflow run id.

Why:
- MLflow gives experiment tracking, reproducibility, and auditability.

### `train_financial_forecast(...)`

This is the full ML training pipeline:
1. Build features.
2. Validate enough history exists.
3. Run walk-forward validation.
4. Forecast future horizon.
5. Detect anomalies.
6. Create monitoring snapshot.
7. Generate unique model version.
8. Build response payload with metrics, forecast, anomalies, params.
9. Log to MLflow.
10. Return `ForecastTrainingResult`.

This is the method to explain if asked "how did you implement ML forecasting?"

### `rows_from_financial_metrics(metrics)`

Converts SQLAlchemy model objects into dictionaries expected by the ML functions.

## 5. Decision Intelligence: `decision_intelligence.py`

This file adds business explanation and uncertainty on top of forecasting.

### `bootstrap_prediction_intervals(actuals, predictions, point_forecast)`

Uses residual bootstrapping:
1. Calculate historical forecast errors.
2. Randomly sample errors with replacement.
3. Add sampled errors to point forecast.
4. Return p05, p50, p95.

Why:
- It estimates uncertainty from real historical model errors.
- Finance users need ranges, not only point estimates.

### `cusum_drift_score(actuals, predictions)`

CUSUM means cumulative sum control chart.

How:
- Convert errors into standardized errors.
- Accumulate positive and negative shifts.
- If max cumulative shift exceeds threshold, drift is detected.

Why:
- Detects persistent bias, not just one bad prediction.

### `driver_attribution(df, target)`

Creates simple explainability by comparing latest feature values against historical averages:
- trend momentum
- seasonality
- recent level
- short-window mean
- volatility

It returns contribution percentages and direction.

Why:
- It gives finance users a reason behind the forecast movement.
- It is not SHAP, but it is transparent and easy to explain.

### `build_decision_intelligence_report(...)`

Combines:
- forecast training
- champion vs baseline comparison
- bootstrap interval
- CUSUM drift
- anomaly count
- estimated anomaly impact
- top drivers
- recommendation

This is the executive AI report layer.

## 6. Alternative XGBoost Forecaster: `xgboost_forecaster.py`

This is a simpler XGBoost-style forecast.

### `_feature_frame(rows, target)`

Creates:
- month
- quarter
- seasonality sine wave
- revenue lag 1
- revenue lag 3
- expense
- expense lag 1
- growth rate

### `train_xgboost_style_forecast(...)`

Steps:
1. Requires at least 8 rows.
2. Builds feature frame.
3. Splits last 1 or 3 rows as test.
4. Uses XGBoost if available, otherwise GradientBoostingRegressor.
5. Calculates MAE, RMSE, MAPE.
6. Predicts next value from latest row.
7. Returns confidence interval and feature importance.

Use this in interview as:

> I also created a lightweight XGBoost-compatible forecast path for fast model output and feature importance, while the main `forecasting_service.py` is the more complete production-style pipeline.

## 7. Prophet Forecasting Utility: `utils/forecasting.py`

### `rolling_forecast(df, months=12)`

Uses Prophet:
- `yearly_seasonality=True`
- no weekly/daily seasonality
- monthly frequency `MS`

Input:
- DataFrame with columns `ds` and `y`.

Output:
- `ds`, `yhat`, `yhat_lower`, `yhat_upper`

Why Prophet:
- Prophet is good for business time-series with trend and seasonality.
- It gives confidence intervals.
- It is easy to use for monthly FP&A forecasts.

### `forecast_revenue`, `forecast_expense`

Thin wrappers around `rolling_forecast`.

### `incorporate_actuals`

Adds new actuals, removes duplicate dates, sorts, and reruns forecast.

## 8. Monte Carlo Scenario Algorithm: `utils/monte_carlo.py`

### `monte_carlo_simulation(drivers, volatility=0.1, simulations=1000)`

For each simulation:
- For each driver, multiply value by random normal factor:
  - `value * np.random.normal(1, volatility)`

Returns:
- mean
- min
- max

Why:
- Scenario planning needs uncertainty.
- Monte Carlo creates many possible outcomes by varying key drivers.

Interview example:

> For base case I used 10 percent volatility, optimistic 5 percent, and pessimistic 20 percent. This lets us show a range of possible revenue and expense outcomes instead of one deterministic number.

## 9. Agent System

There are two orchestrator styles:

1. `agents/orchestrator_agent.py`
   - Uses concrete agent classes.
   - Runs forecasting, scenario, budget, KPI, variance, report, email.

2. `services/agentic_system.py`
   - LangGraph-style deterministic orchestration.
   - Stores traces, reflections, evals, recommendations, observability.

### Revenue Forecast Agent

File: `agents/revenue_agent.py`

`run(company_id, db)`:
1. Query financial rows for company.
2. For each row, calculate driver revenue:
   - `customer_count * price_per_customer`
3. If driver revenue is invalid, fall back to actual revenue.
4. Skip invalid rows.
5. Smooth using 3-period rolling mean.
6. Forecast 12 months with Prophet.
7. Return forecast.

Why driver-based:
- Revenue is often driven by volume and price.
- `customer_count * price_per_customer` is more explainable than blindly forecasting revenue.

`adjust_forecast(forecast, variance)`:
- Converts percentage if given as percent instead of ratio.
- Applies factor `1 - pct`.
- Updates `yhat`.

Why:
- Creates a feedback loop from variance analysis into future forecast.

### Expense Forecast Agent

File: `agents/expense_agent.py`

`run(company_id, db)`:
1. Query financial rows.
2. Calculate COGS.
3. Calculate gross profit if missing.
4. Calculate operating expense as `gross_profit - ebitda`.
5. Forecast COGS separately.
6. Forecast OPEX separately.
7. Merge forecasts by date.
8. Total expense = forecasted COGS + forecasted OPEX.

Why separate COGS/OPEX:
- Cost of goods and operating expenses behave differently.
- Separating them is more realistic than one total-expense model.

### Scenario Modeling Agent

File: `agents/scenario_agent.py`

`run(base_revenue, base_expense)`:
- Builds drivers.
- Runs Monte Carlo with:
  - optimistic: 5 percent volatility
  - base: 10 percent
  - pessimistic: 20 percent
- Broadcasts result over WebSocket.

### Variance Explanation Agent

File: `agents/variance_agent.py`

`run(actual, forecast, company_id=None)`:
1. Calculate `variance = actual - forecast`.
2. Calculate `pct = variance / forecast`.
3. Build prompt asking for price, volume, mix, timing explanation.
4. If `GROQ_API_KEY` is missing:
   - Use deterministic fallback:
     - >=15 percent variance: volume
     - >=7 percent: price
     - otherwise timing
5. If Groq key exists:
   - Calls Groq Llama `llama-3.3-70b-versatile`.
6. Returns variance, percentage, explanation.

Important interview honesty:

> The LLM is used only for narrative explanation, not for calculating financial numbers. The variance math is deterministic. If the API key is absent, the system still works with a rule-based fallback.

### KPI Tracking Agent

`run(company_id, db)`:
- Calls `get_kpis`.
- Broadcasts KPI status.

KPI status logic:
- actual/target >= 1: green
- actual/target >= 0.9: yellow
- otherwise red

### Budget Builder Agent

`run(revenue_forecast, expense_forecast)`:
- Aligns revenue and expense forecast by index.
- Calculates:
  - profit = revenue - expense
  - profit margin = profit / revenue
- Adds flags:
  - `Loss-making` if margin < 0
  - `Aggressive growth assumption` if revenue jumps >25 percent from previous forecast month.

### Capital Planning Agent

`run(db, rate=0.1)`:
- Reads initiatives.
- Creates cashflows:
  - initial negative investment
  - ramped expected returns
- Calculates NPV and IRR.

`npv(rate, cashflows)`:
- Discounts each cashflow by `(1 + rate) ** period`.

`irr(cashflows)`:
- Uses `numpy_financial.irr`.

Why:
- NPV tells value today.
- IRR gives implied return rate.
- These are standard finance capital allocation metrics.

### Strategic Initiative Agent

Similar to capital planning, but includes progress:
- progress = weeks elapsed / total initiative period
- adjusted cashflows depend on progress
- returns ROI, NPV, IRR, progress.

### Reporting Agent

`generate_board_pack(filename, db)`:
- Uses ReportLab to generate PDF.
- For each company:
  - Adds company name.
  - Calculates revenue growth.
  - Adds KPI table.
  - Adds initiative ROI lines.

Why:
- Produces board-ready output from the same underlying finance data.

## 10. Concrete Orchestrator: `agents/orchestrator_agent.py`

### `run_planning_cycle(company_id=None, company_name=None, db=None, notify_email=None)`

Flow:
1. Validate company id/name and DB session.
2. Resolve company name to id if needed.
3. Create all agents.
4. Run revenue, expense, and capital agents concurrently with `asyncio.gather`.
5. Run initiative agent.
6. Use latest forecast values for scenario modeling.
7. Scenario adjustment:
   - Takes base scenario mean.
   - Calculates revenue and expense adjustment factors.
   - Scales forecasts.
8. Build budget.
9. Run KPIs.
10. Load financial rows.
11. Run variance analysis against latest actual and latest forecast.
12. If variance exceeds `KPI_ALERT_THRESHOLD`, adjust forecast.
13. Generate insight text.
14. Generate board-pack PDF.
15. If email is configured and there is high variance or red KPI:
   - Render Jinja template.
   - Send email via SendGrid.
16. Return all outputs.

Why this is designed well:
- Agents are modular.
- Forecasting, KPI, scenario, reporting, and email are separated.
- `asyncio.gather` speeds independent agent calls.
- The forecast feedback loop reacts to variance.
- Email only triggers on meaningful risk, reducing alert noise.

## 11. Traced Agentic System: `services/agentic_system.py`

This is the interview feature for "agentic AI".

### `AGENT_GRAPH`

Defines the planning workflow:
- Orchestrator
- Revenue Forecasting
- Expense Forecasting
- KPI Monitoring
- Variance Analysis
- Scenario Modeling
- Budget Validation
- Capital Planning
- Risk Detection
- Reporting
- Reflection
- Evaluation

### `_estimate_tokens(payload)`

Rough token estimate using `len(str(payload)) / 4`.

Why:
- Gives observability and estimated cost even without a real LLM call.

### `_trace(...)`

Stores each agent step in `AgentTrace`:
- agent name
- thought
- tool call
- input
- output
- decision
- latency
- tokens
- cost
- success

Why:
- Makes agent behavior explainable and auditable.

### `_forecast(values)`

Simple deterministic fallback forecast:
1. Clean values.
2. Calculate growth rates between consecutive periods.
3. Average last 6 growth rates.
4. Forecast next value as `last * (1 + growth)`.
5. Confidence decreases as growth becomes extreme.

Why:
- Lightweight fallback if full ML is not needed.
- Easy to explain and deterministic.

### `_quality_checks(rows)`

Checks:
- duplicate periods
- negative revenue
- missing revenue

Returns score out of 100.

### `run_agentic_cycle(db, company_id, request_type)`

Flow:
1. Create `AgentRun`.
2. Load company, financial rows, KPIs.
3. Store orchestrator trace.
4. Produce revenue forecast.
5. Produce expense forecast.
6. Identify red KPIs.
7. Calculate latest revenue variance.
8. Create delegated agent steps:
   - revenue forecast
   - expense forecast
   - KPI scan
   - variance explanation
   - scenarios
   - budget validation
   - capital planning
   - risk detection
   - reporting outline
9. Store a trace for each delegated agent.
10. Store reflection.
11. Create recommendation.
12. Store evaluation rows:
   - forecast schema validity
   - data quality score
   - tool call success rate
   - hallucination risk
13. Mark run complete.
14. Broadcast completion through WebSocket.

Important:
- This is called "LangGraph-style" but it is deterministic custom orchestration, not actual LangGraph runtime.

Interview sentence:

> I implemented the agent graph deterministically so that every step is reproducible and auditable. Each agent output is stored as a trace with input, output, latency, tokens, and decision.

### `list_agent_runs` and `get_agent_run`

Expose run history, traces, reflections, and evals to the frontend Agent Intelligence page.

## 12. Financial API: `api/financials.py`

Endpoints:

### `GET /financials/{company_id}/history`

Returns historical financial rows.

### `GET /financials/{company_id}/forecast`

Runs agent-based revenue, expense, and capital forecasts.

### `GET /financials/{company_id}/ml-forecast`

Runs main ML forecast without necessarily saving it.

Query params:
- `target`
- `horizon`
- `persist`

If `persist=true`, saves experiment, forecast points, anomalies, and monitoring.

### `POST /financials/{company_id}/ml-forecast/train`

Runs and always persists ML forecast training.

### `GET /financials/{company_id}/ml-experiments`

Returns last 20 persisted forecast experiments.

### `GET /financials/{company_id}/anomalies`

Returns persisted anomaly flags.

### `GET /financials/{company_id}/model-monitoring`

Returns model monitoring snapshots.

### `POST /financials/upload-financials`

Uploads CSV:
1. Saves temp file.
2. Loads financial CSV into DB.
3. Resolves companies in CSV.
4. Runs planning cycle for each company.
5. Deletes temp file.

### `_persist_forecast_run(db, payload)`

Persists:
- `ForecastExperiment`
- `ForecastPoint`
- `AnomalyFlag`
- `ModelMonitoringSnapshot`

Uses uniqueness check for anomalies so duplicate anomaly records are updated, not duplicated.

## 13. Other Important APIs

### `api/agents.py`

Key endpoints:
- `/agents/graph`: returns agent graph definition.
- `/agents/run-cycle`: runs traced agentic cycle.
- `/agents/runs`: lists runs.
- `/agents/runs/{run_id}`: run detail with traces/reflections/evals.
- `/agents/observability/summary`: token, latency, success, eval metrics.
- `/agents/mcp`: describes MCP-style tools.
- `/agents/evals/{run_id}`: reruns evaluations.
- `/agents/recommendations`: recommendations.
- `/agents/data-sources`: connectors.
- `/agents/pipelines/run`: Python ETL.
- `/agents/pipelines/beam/run`: Apache Beam.
- `/agents/pipelines/spark/run`: Spark.
- `/agents/tools/execute`: RBAC-secured tool execution.

### `api/scenarios.py`

Lets frontend run scenarios from:
- direct assumptions
- latest company financials

### `api/orchestrator.py`

`POST /orchestrator/run/{company_id}` runs the concrete planning cycle.

### `api/reports.py`

Generates board pack PDF and CSV exports.

### `api/platform.py`

Readiness, live operations, network protocols, capacity, partitions, outbox, idempotent planning job.

### `api/integrations.py`

Salesforce and Oracle health/sync/demo endpoints.

## 14. Services

### `financial_service.py`

`generate_financial_forecast`:
- Runs revenue, expense, and capital agents concurrently.
- Returns sanitized JSON.

`get_financial_history`:
- Returns financial rows for frontend charts.

### `kpi_service.py`

Calculates KPI status using actual/target ratio.

### `initiative_service.py`

Returns initiatives and ROI.

### `enterprise_system.py`

Handles:
- recommendations
- data source seed/list
- connector test/sync
- pipeline run
- RBAC-secured tools
- observability summary

### RBAC logic

Roles:
- Viewer
- Finance Analyst
- CFO
- Admin

Tools are allowed/blocked based on role. Every tool call is logged in `ToolAuditLog`.

Why:
- Finance tools can expose sensitive data or create recommendations, so access must be controlled and audited.

## 15. Connectors

### Base connector

Defines common interface:
- `test_connection`
- `sync`

### CSV connector

Mock sync of seeded CSV financial files.

### Salesforce connector

Supports mock and real mode.

Real mode:
- OAuth password flow.
- SOQL query accounts and opportunities.
- Handles pagination through `nextRecordsUrl`.
- Normalizes opportunities:
  - amount
  - probability
  - weighted amount
  - fiscal quarter
  - forecast category

Why weighted pipeline:
- Revenue forecast should consider probability-weighted opportunities, not raw pipeline only.

### Oracle connector

Supports mock and real mode.

Real mode:
- Uses `oracledb`.
- Runs query against ERP financial actuals.

Why:
- FP&A data usually comes from ERP systems like Oracle.

## 16. Data Pipelines

### `extract.py`

Reads seeded financials from DB into rows.

### `quality_checks.py`

Checks duplicates, missing values, negative revenue, invalid period, statistical outliers.

Quality score:
- Starts at 100.
- Subtracts penalties.

### `transform.py`

Creates warehouse-style output:
- raw financial uploads
- staging financials
- fact financials
- dim company
- dim time

Calculates:
- gross margin
- EBITDA margin

### `load.py`

Creates `PipelineRun` with counts and quality results.

### `beam_pipeline.py`

Runs the extract-transform-quality-load sequence in Python and labels it as Beam-style.

Why:
- Shows data engineering readiness and warehouse modeling.

## 17. Frontend Feature Map

### `App.tsx`

Routes:
- `/`: portfolio dashboard
- `/company/:id`: company detail
- `/scenarios`: scenario builder
- `/kpis`: KPI scorecard
- `/reports`: reports and exports
- `/emails`: email center
- `/agents`: agent intelligence
- `/admin`: RBAC/admin

### `api/client.ts`

Central fetch wrapper:
- Reads base URL from env.
- Adds JSON headers.
- Throws useful error on non-200.
- Supports blobs for PDF/CSV exports.

### Agent Intelligence page

Shows:
- agent runs
- ReAct trace timeline
- observability metrics
- evals
- recommendations
- data sources
- pipeline runs
- Beam/Spark actions
- MCP-style secure tool execution

This page demonstrates explainable AI operations.

## 18. What To Say About AI/ML Services

Use this exact answer:

> The AI/ML layer has three parts. First, statistical forecasting using Prophet for revenue and expense agents. Second, a production-style tabular ML forecaster using XGBoost or Gradient Boosting with lag, rolling, trend, and seasonality features. It uses walk-forward validation, compares against Prophet or seasonal naive baseline, generates prediction intervals, detects anomalies with rolling z-score plus Isolation Forest, and logs experiments to MLflow. Third, an agentic decision layer that coordinates finance agents, stores traces, generates recommendations, runs evals, and optionally uses Groq Llama for natural-language variance explanation.

## 19. Key Algorithms To Explain

### Prophet

Used for revenue/expense agent forecasts.
- Good for time-series trend and seasonality.
- Produces `yhat`, `yhat_lower`, `yhat_upper`.

### XGBoost / Gradient Boosting

Used for tabular financial forecasting.
- Learns nonlinear relationships.
- Works well with engineered features.
- Fallback ensures system runs even without XGBoost.

### Walk-forward validation

Used instead of random split.
- Train on past.
- Predict next period.
- Repeat.

### Seasonal naive baseline

Baseline uses same month last year or last value.
- Helps prove ML is better than simple forecasting.

### Rolling z-score

Detects unusual values relative to recent average and volatility.

### Isolation Forest

Unsupervised anomaly detection.
- Isolates unusual points in multidimensional feature space.

### CUSUM drift detection

Detects persistent forecast bias over time.

### Bootstrap prediction interval

Samples historical residuals to estimate uncertainty range.

### Monte Carlo simulation

Runs many random variations of revenue/expense assumptions.
- Optimistic, base, pessimistic scenarios.

### NPV and IRR

Capital planning metrics.
- NPV discounts future cashflows.
- IRR calculates return rate where NPV is zero.

### KPI thresholding

Business rule:
- green >= 100 percent of target
- yellow >= 90 percent
- red < 90 percent

## 20. Honest Limitations To Mention

Say this if asked:

> Some integrations run in mock mode by default so the project can be demonstrated without real enterprise credentials. The architecture supports real Salesforce and Oracle connections when credentials and mock mode settings are changed. The agent graph is LangGraph-style deterministic orchestration rather than a deployed LangGraph runtime. This was intentional because finance workflows need reproducibility, auditability, and predictable behavior.

## 21. Interview Defense: Why These Decisions Are Correct

1. FastAPI:
   - Fast async API framework.
   - Automatic docs.
   - Good for ML service endpoints.

2. SQLAlchemy/PostgreSQL:
   - Reliable relational modeling for finance data.
   - SQLAlchemy keeps DB access clean.

3. TimescaleDB attempt:
   - Financial metrics are time-series.
   - Hypertables improve time-series query patterns.

4. XGBoost:
   - Strong for tabular data.
   - Handles nonlinear financial drivers.

5. Prophet:
   - Simple, explainable time-series model.
   - Useful for business seasonality.

6. Walk-forward validation:
   - Prevents time leakage.
   - Matches real forecast process.

7. Baseline comparison:
   - Prevents useless ML.
   - Proves model value.

8. MLflow:
   - Tracks experiments and metrics.
   - Supports model governance.

9. Agent traces:
   - Finance AI needs audit trail.
   - Users can see why recommendations were made.

10. Mock connectors:
   - Lets demo run anywhere.
   - Same interface can switch to real systems.

11. RBAC and audit logs:
   - Important for finance/security.
   - Sensitive actions are controlled and logged.

12. Separate revenue/expense/capital/KPI agents:
   - Modular design.
   - Each agent has single responsibility.

## 22. Common Interview Questions and Answers

### Q: How is revenue forecast implemented?

Answer:

> Revenue forecast uses two paths. The agent path first tries driver-based revenue, customer count multiplied by price per customer, and falls back to actual revenue. It smooths using a 3-period rolling average and forecasts 12 months with Prophet. The ML path builds a feature frame with calendar, seasonality, trend, lag, rolling, and decomposition features, then trains XGBoost or Gradient Boosting with walk-forward validation.

### Q: How do you prevent data leakage?

Answer:

> I used walk-forward validation. Each fold trains only on periods before the test period. Rolling features are shifted before calculation, so the current target is not used to predict itself.

### Q: What happens if XGBoost is not installed?

Answer:

> The code falls back to sklearn GradientBoostingRegressor. This keeps the service usable in lightweight environments while preserving the same interface.

### Q: How do you detect anomalies?

Answer:

> I combine rolling z-score and Isolation Forest. Z-score catches values that deviate from recent mean and volatility. Isolation Forest catches unusual multidimensional patterns using target, lag, rolling, and seasonal features. The final anomaly score takes the stronger signal.

### Q: Where is LLM used?

Answer:

> The LLM is used in the Variance Explanation Agent through Groq Llama. It creates a board-ready explanation of actual vs forecast variance across price, volume, mix, and timing. The numerical calculation is deterministic, and there is a rule-based fallback if no Groq key is configured.

### Q: Is the agent system actually autonomous?

Answer:

> It is autonomous within a controlled finance workflow. The orchestrator delegates to specialist agents, collects results, adjusts forecasts based on variance, generates reports, and sends alerts. But it is deterministic and auditable, which is safer for finance than uncontrolled autonomous actions.

### Q: How is model monitoring done?

Answer:

> The service calculates rolling recent MAE, RMSE, and MAPE from validation folds. If rolling MAPE exceeds a threshold, it marks retraining as recommended and stores a monitoring snapshot.

### Q: How are scenarios generated?

Answer:

> Scenarios use Monte Carlo simulation. The system perturbs revenue and expense drivers with normal random noise. Optimistic uses lower volatility, base uses medium volatility, and pessimistic uses higher volatility. It returns mean, min, and max.

### Q: What is the data pipeline?

Answer:

> It extracts financial records, runs quality checks, transforms data into warehouse-style fact and dimension tables, calculates financial margins, and logs a pipeline run with row counts and quality score. There are Python, Apache Beam, and Spark options.

### Q: Why store traces?

Answer:

> Agent traces make the AI workflow explainable. For every step we store the agent name, thought, tool call, input, output, decision, latency, tokens, cost, and success. That is important for debugging, trust, and auditability.

## 23. One-Minute Project Summary

> This is an Autonomous FP&A platform. I built a FastAPI backend with PostgreSQL data models for companies, financial metrics, KPIs, initiatives, forecasts, anomalies, agent traces, and recommendations. The AI/ML layer forecasts revenue, expense, cash flow, EBITDA and other targets using XGBoost or Gradient Boosting with lag, rolling, trend, and seasonality features. It uses walk-forward validation, compares against a Prophet or seasonal naive baseline, detects anomalies with z-score plus Isolation Forest, monitors drift, and logs experiments with MLflow. The agent layer coordinates revenue, expense, KPI, variance, scenario, budget, capital planning, and reporting agents. Variance explanations can use Groq Llama, with deterministic fallback. The platform also includes Monte Carlo scenarios, NPV/IRR capital planning, RBAC-secured tools, audit logs, enterprise connectors, ETL pipelines, board-pack PDF generation, email alerts, and a React dashboard for observability and agent traces.

