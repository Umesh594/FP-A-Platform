import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.connectors.oracle_connector import OracleConfig, OracleFinanceConnector, OracleIntegrationError


def test_oracle_mock_connector_returns_financial_actuals():
    connector = OracleFinanceConnector(
        config=OracleConfig(
            dsn="",
            username="",
            password="",
            schema="FPNA",
            timeout_seconds=10,
            mock_mode=True,
        )
    )

    result = connector.test_connection()
    rows = connector.fetch_financial_actuals()

    assert result.status == "connected"
    assert result.rows_available == 3
    assert len(rows) == 3
    assert {row["account"] for row in rows} == {"REVENUE", "COGS", "EBITDA"}


def test_oracle_connector_requires_credentials_when_mock_mode_disabled():
    connector = OracleFinanceConnector(
        config=OracleConfig(
            dsn="",
            username="",
            password="",
            schema="FPNA",
            timeout_seconds=10,
            mock_mode=False,
        )
    )

    try:
        connector.test_connection()
    except OracleIntegrationError as exc:
        assert "Oracle DSN" in str(exc)
    else:
        raise AssertionError("Expected Oracle config validation to fail")
