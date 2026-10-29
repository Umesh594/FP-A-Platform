import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://postgres:1234@localhost:5432/db1")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.connectors.mysql_finance_connector import MySQLFinanceConfig, MySQLFinanceConnector
from app.observability.splunk_hec import build_hec_event


def test_mysql_mock_connector_exposes_validated_finance_rows():
    connector = MySQLFinanceConnector(config=MySQLFinanceConfig("localhost", 3306, "fpa", "reader", "", 1, True))
    result = connector.test_connection()
    rows = connector.fetch_financial_actuals()
    assert result.rows_available == 3
    assert [row["account"] for row in rows] == ["REVENUE", "COGS", "EBITDA"]


def test_splunk_hec_event_uses_structured_redacted_fields():
    event = build_hec_event("request_completed", {"status_code": 200, "email": "[email]"})
    assert event["event"]["event_name"] == "request_completed"
    assert event["event"]["status_code"] == 200
