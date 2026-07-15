# Production Reliability Additions

This project now includes a platform reliability layer that turns the FP&A app into a stronger product-company resume project.

For high-frequency trading or quant engineering firms, use this as supporting systems experience rather than direct trading experience. See `RESUME_HFT_PROJECTS.md` for the HFT-specific shortlist, resume bullets, and what not to overclaim.

## Implemented Capabilities

- Idempotent API workflow for planning job creation using `Idempotency-Key`, request hashing, replay detection, and conflict handling.
- Reliable outbox pattern for async planning events, with pending/processed state, retry metadata, worker ownership, and Celery draining.
- Distributed lock abstraction using Redis `SET NX EX` with Postgres advisory lock fallback.
- Postgres/TimescaleDB capacity observability for database size, active connections, time-series row volume, and pending outbox backlog.
- Readiness checks for Postgres and Redis dependencies.
- TimescaleDB partition reporting for the `financial_metrics` hypertable.
- Financial forecasting service with lag features, rolling-window statistics, calendar flags, seasonality features, walk-forward validation, and champion-vs-baseline model comparison.
- Anomaly detection for financial line items using Isolation Forest plus rolling z-score control-chart signals.
- Model monitoring snapshots with rolling MAPE/RMSE/MAE and retrain triggers when rolling MAPE exceeds threshold.
- Experiment tracking tables plus optional MLflow run logging for model params, versions, and metrics.
- Unit tests for deterministic hashing and idempotent replay semantics.

## Resume Bullets

- Built production reliability primitives for a FastAPI, Postgres/TimescaleDB, Redis, and Celery FP&A platform, including idempotent job APIs, distributed locking, and transactional outbox processing.
- Implemented database capacity management APIs tracking Postgres size, connection pressure, TimescaleDB financial metric volume, and async backlog health.
- Designed fault-tolerant async planning workflow with Celery primary delivery and durable outbox fallback to prevent duplicate or lost planning jobs.
- Added readiness and partition observability endpoints to support cloud-style operations, reliability monitoring, and scale diagnostics.

## Senior Data Scientist Resume Bullets

```latex
\item Built a production financial forecasting layer over TimescaleDB using XGBoost-style gradient boosting with \textbf{19 lag, rolling-window, calendar, and seasonality features}, reducing sample revenue forecast MAPE from \textbf{15.86\% seasonal baseline to 1.50\% champion model}.
\vspace{-5pt}

\item Implemented proper time-series validation with \textbf{28 walk-forward folds} and automated \textbf{MAPE/RMSE/MAE} reporting across revenue, expense, cash-flow, EBITDA and gross-profit targets through FastAPI ML endpoints.
\vspace{-5pt}

\item Added unsupervised anomaly detection for financial line items using \textbf{Isolation Forest + rolling z-score control charts}, persisting anomaly severity, expected value, score and method for the \textbf{50 most recent flagged periods}.
\vspace{-5pt}

\item Operationalized model lifecycle monitoring with persisted experiment versions, optional \textbf{MLflow} run logging and weekly retrain checks that trigger when rolling MAPE exceeds a configurable \textbf{15\% drift threshold}.
```

## Interview Talking Points

- Idempotency prevents duplicate planning jobs when clients retry after timeouts.
- The outbox pattern makes job creation durable before async processing starts.
- Redis locks are fast for distributed workers, while Postgres advisory locks provide a database-native fallback.
- TimescaleDB hypertables partition financial time-series data by period, which improves retention, scan efficiency, and operational observability.
- Capacity endpoints model Azure-style thinking: monitor resource limits before they become customer-facing reliability incidents.
- Walk-forward validation avoids random train/test leakage and better simulates how forecasts perform as new monthly actuals arrive.
- Monitoring snapshots turn model quality into an operational signal, not a notebook-only metric.

## Useful Endpoints

- `GET /platform/ready`
- `GET /platform/capacity`
- `GET /platform/partitions`
- `POST /platform/planning-jobs` with `Idempotency-Key`
- `POST /platform/outbox/drain`
- `GET /financials/{company_id}/ml-forecast`
- `POST /financials/{company_id}/ml-forecast/train`
- `GET /financials/{company_id}/ml-experiments`
- `GET /financials/{company_id}/anomalies`
- `GET /financials/{company_id}/model-monitoring`
