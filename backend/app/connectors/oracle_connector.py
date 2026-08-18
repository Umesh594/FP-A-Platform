from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import settings
from app.connectors.base import BaseConnector, ConnectorResult


class OracleIntegrationError(RuntimeError):
    pass


@dataclass
class OracleConfig:
    dsn: str
    username: str
    password: str
    schema: str
    timeout_seconds: int
    mock_mode: bool


class OracleFinanceConnector(BaseConnector):
    source_type = "oracle"

    def __init__(self, name: str = "oracle-finance", config: OracleConfig | None = None):
        super().__init__(name)
        self.config = config or OracleConfig(
            dsn=settings.ORACLE_DSN,
            username=settings.ORACLE_USERNAME,
            password=settings.ORACLE_PASSWORD,
            schema=settings.ORACLE_SCHEMA,
            timeout_seconds=settings.ORACLE_TIMEOUT_SECONDS,
            mock_mode=settings.ORACLE_MOCK_MODE,
        )

    def test_connection(self) -> ConnectorResult:
        if self.config.mock_mode:
            return ConnectorResult(
                self.name,
                self.source_type,
                "connected",
                3,
                "Oracle finance connector running in mock mode with 3 validated ERP rows",
            )

        if not self.config.dsn or not self.config.username or not self.config.password:
            raise OracleIntegrationError("Oracle DSN, username and password are required when mock mode is disabled")

        import oracledb

        with oracledb.connect(
            user=self.config.username,
            password=self.config.password,
            dsn=self.config.dsn,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM dual")
                cursor.fetchone()

        return ConnectorResult(self.name, self.source_type, "connected", 1, "Oracle ERP connection validated")

    def sync(self) -> ConnectorResult:
        rows = self.fetch_financial_actuals()
        return ConnectorResult(
            self.name,
            self.source_type,
            "synced",
            len(rows),
            f"Oracle finance actuals synced from schema {self.config.schema}",
        )

    def fetch_financial_actuals(self) -> list[dict[str, Any]]:
        if self.config.mock_mode:
            return [
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "REVENUE", "amount": 2080000.0},
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "COGS", "amount": 760000.0},
                {"company_code": "FINTECH_PAY", "period": "2026-01", "account": "EBITDA", "amount": 482000.0},
            ]

        import oracledb

        query = f"""
            SELECT company_code, period_name, account_code, actual_amount
            FROM {self.config.schema}.financial_actuals
            WHERE period_name >= ADD_MONTHS(TRUNC(SYSDATE, 'MM'), -12)
        """
        with oracledb.connect(
            user=self.config.username,
            password=self.config.password,
            dsn=self.config.dsn,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                return [
                    {
                        "company_code": row[0],
                        "period": row[1],
                        "account": row[2],
                        "amount": float(row[3]),
                    }
                    for row in cursor.fetchall()
                ]
