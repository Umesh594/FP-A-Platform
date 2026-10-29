from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.connectors.base import BaseConnector, ConnectorResult


class MySQLIntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class MySQLFinanceConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    timeout_seconds: int
    mock_mode: bool


class MySQLFinanceConnector(BaseConnector):
    """Read-only MySQL finance source used by the FP&A ingestion layer."""

    source_type = "mysql"

    def __init__(self, name: str = "mysql-finance", config: MySQLFinanceConfig | None = None):
        super().__init__(name)
        self.config = config or MySQLFinanceConfig(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            database=settings.MYSQL_DATABASE,
            username=settings.MYSQL_USERNAME,
            password=settings.MYSQL_PASSWORD,
            timeout_seconds=settings.MYSQL_TIMEOUT_SECONDS,
            mock_mode=settings.MYSQL_MOCK_MODE,
        )

    def test_connection(self) -> ConnectorResult:
        if self.config.mock_mode:
            return ConnectorResult(self.name, self.source_type, "connected", 3, "MySQL finance connector running with 3 validated source rows")
        self._query("SELECT 1")
        return ConnectorResult(self.name, self.source_type, "connected", 1, "MySQL finance connection validated")

    def sync(self) -> ConnectorResult:
        rows = self.fetch_financial_actuals()
        return ConnectorResult(self.name, self.source_type, "synced", len(rows), "MySQL financial actuals synced")

    def fetch_financial_actuals(self) -> list[dict[str, Any]]:
        if self.config.mock_mode:
            return [
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "REVENUE", "amount": 2080000.0},
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "COGS", "amount": 760000.0},
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "EBITDA", "amount": 482000.0},
            ]
        return self._query(
            """
            SELECT company_code, period_name AS period, account_code AS account, actual_amount AS amount
            FROM financial_actuals
            WHERE period_name >= DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 12 MONTH), '%Y-%m')
            ORDER BY period_name, account_code
            """
        )

    def _query(self, query: str) -> list[dict[str, Any]]:
        if not self.config.password:
            raise MySQLIntegrationError("MYSQL_PASSWORD is required when MYSQL_MOCK_MODE is disabled")
        try:
            import pymysql

            with pymysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                connect_timeout=self.config.timeout_seconds,
                cursorclass=pymysql.cursors.DictCursor,
                read_timeout=self.config.timeout_seconds,
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query)
                    return list(cursor.fetchall())
        except MySQLIntegrationError:
            raise
        except Exception as exc:
            raise MySQLIntegrationError("MySQL finance query failed") from exc
