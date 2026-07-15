from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    request_type = Column(String, nullable=False)
    status = Column(String, default="running", nullable=False)
    final_output = Column(JSON, nullable=True)
    latency_ms = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    traces = relationship("AgentTrace", back_populates="run")
    reflections = relationship("AgentReflection", back_populates="run")
    evals = relationship("EvalRun", back_populates="run")


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.run_id"), index=True, nullable=False)
    agent_name = Column(String, index=True, nullable=False)
    step_type = Column(String, nullable=False)
    thought = Column(Text, nullable=True)
    tool_name = Column(String, nullable=True)
    tool_input = Column(JSON, nullable=True)
    tool_output = Column(JSON, nullable=True)
    decision = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("AgentRun", back_populates="traces")


class AgentReflection(Base):
    __tablename__ = "agent_reflections"

    id = Column(Integer, primary_key=True)
    run_id = Column(String, ForeignKey("agent_runs.run_id"), index=True, nullable=False)
    agent_name = Column(String, index=True, nullable=False)
    original_output = Column(JSON, nullable=True)
    critique = Column(Text, nullable=False)
    revised_output = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("AgentRun", back_populates="reflections")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), index=True, nullable=False)
    recommendation_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    reasoning = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0)
    expected_impact = Column(String, nullable=False)
    status = Column(String, default="open", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True)
    agent_run_id = Column(String, ForeignKey("agent_runs.run_id"), index=True, nullable=False)
    metric_name = Column(String, nullable=False)
    score = Column(Float, default=0)
    passed = Column(Boolean, default=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    run = relationship("AgentRun", back_populates="evals")


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    status = Column(String, default="configured", nullable=False)
    config = Column(JSON, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True)
    pipeline_name = Column(String, nullable=False)
    status = Column(String, default="running", nullable=False)
    rows_extracted = Column(Integer, default=0)
    rows_loaded = Column(Integer, default=0)
    quality_score = Column(Float, default=0)
    checks = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class ToolAuditLog(Base):
    __tablename__ = "tool_audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, default="demo-user", nullable=False)
    role = Column(String, default="Admin", nullable=False)
    tool_name = Column(String, nullable=False)
    tool_input = Column(JSON, nullable=True)
    allowed = Column(Boolean, default=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RawFinancialUpload(Base):
    __tablename__ = "raw_financial_uploads"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, nullable=True)
    payload = Column(JSON, nullable=False)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StagingFinancial(Base):
    __tablename__ = "staging_financials"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    period = Column(DateTime, index=True, nullable=False)
    revenue = Column(Float, default=0)
    cogs = Column(Float, default=0)
    gross_profit = Column(Float, default=0)
    ebitda = Column(Float, default=0)
    validation_status = Column(String, default="valid", nullable=False)


class FactFinancial(Base):
    __tablename__ = "fact_financials"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    time_key = Column(String, index=True, nullable=False)
    revenue = Column(Float, default=0)
    cogs = Column(Float, default=0)
    gross_profit = Column(Float, default=0)
    ebitda = Column(Float, default=0)
    gross_margin = Column(Float, default=0)
    ebitda_margin = Column(Float, default=0)


class DimCompany(Base):
    __tablename__ = "dim_company"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=True)


class DimTime(Base):
    __tablename__ = "dim_time"

    id = Column(Integer, primary_key=True)
    time_key = Column(String, unique=True, index=True, nullable=False)
    month = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)


class DimDepartment(Base):
    __tablename__ = "dim_department"

    id = Column(Integer, primary_key=True)
    department_name = Column(String, unique=True, nullable=False)


class DimKpi(Base):
    __tablename__ = "dim_kpi"

    id = Column(Integer, primary_key=True)
    kpi_name = Column(String, unique=True, nullable=False)
    category = Column(String, default="financial", nullable=False)


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    target = Column(String, nullable=False)
    forecast_value = Column(Float, default=0)
    lower_bound = Column(Float, default=0)
    upper_bound = Column(Float, default=0)
    model_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ForecastExperiment(Base):
    __tablename__ = "forecast_experiments"

    id = Column(Integer, primary_key=True)
    experiment_name = Column(String, index=True, nullable=False)
    model_version = Column(String, unique=True, index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    target = Column(String, index=True, nullable=False)
    champion_model = Column(String, nullable=False)
    baseline_model = Column(String, nullable=False)
    params = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=False)
    feature_summary = Column(JSON, nullable=True)
    mlflow_run_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ForecastPoint(Base):
    __tablename__ = "forecast_points"

    id = Column(Integer, primary_key=True)
    model_version = Column(String, ForeignKey("forecast_experiments.model_version"), index=True, nullable=False)
    company_id = Column(Integer, index=True, nullable=False)
    target = Column(String, index=True, nullable=False)
    period = Column(Date, index=True, nullable=False)
    prediction = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("model_version", "period", name="uq_forecast_point_version_period"),
    )


class AnomalyFlag(Base):
    __tablename__ = "anomaly_flags"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    target = Column(String, index=True, nullable=False)
    period = Column(Date, index=True, nullable=False)
    actual_value = Column(Float, nullable=False)
    expected_value = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String, default="low", nullable=False)
    method = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "target", "period", "method", name="uq_anomaly_company_target_period_method"),
    )


class ModelMonitoringSnapshot(Base):
    __tablename__ = "model_monitoring_snapshots"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    target = Column(String, index=True, nullable=False)
    model_version = Column(String, index=True, nullable=False)
    rolling_mape = Column(Float, nullable=False)
    rolling_rmse = Column(Float, nullable=False)
    rolling_mae = Column(Float, nullable=False)
    threshold_mape = Column(Float, default=0.15, nullable=False)
    retrain_recommended = Column(Boolean, default=False, nullable=False)
    drift_status = Column(String, default="healthy", nullable=False)
    details = Column(JSON, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ScenarioResult(Base):
    __tablename__ = "scenario_results"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, index=True, nullable=False)
    scenario_name = Column(String, nullable=False)
    result_payload = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    request_hash = Column(String, nullable=False)
    endpoint = Column(String, index=True, nullable=False)
    status = Column(String, default="processing", nullable=False)
    response_payload = Column(JSON, nullable=True)
    locked_until = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(Integer, primary_key=True)
    aggregate_type = Column(String, index=True, nullable=False)
    aggregate_id = Column(String, index=True, nullable=False)
    event_type = Column(String, index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String, default="pending", index=True, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    next_attempt_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    locked_by = Column(String, nullable=True)
    locked_until = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)


class CapacitySnapshot(Base):
    __tablename__ = "capacity_snapshots"

    id = Column(Integer, primary_key=True)
    component = Column(String, index=True, nullable=False)
    metric_name = Column(String, index=True, nullable=False)
    metric_value = Column(Float, nullable=False)
    unit = Column(String, default="count", nullable=False)
    threshold = Column(Float, nullable=True)
    status = Column(String, default="healthy", nullable=False)
    details = Column(JSON, nullable=True)
    captured_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("component", "metric_name", "captured_at", name="uq_capacity_metric_capture"),
    )
