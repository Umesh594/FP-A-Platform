from sqlalchemy.orm import Session

from app.connectors.base import BaseConnector, ConnectorResult
from app.models.financials import FinancialMetric


class PostgresConnector(BaseConnector):
    source_type = "postgresql"

    def __init__(self, name: str, db: Session):
        super().__init__(name)
        self.db = db

    def sync(self) -> ConnectorResult:
        rows = self.db.query(FinancialMetric).count()
        return ConnectorResult(self.name, self.source_type, "synced", rows, "PostgreSQL warehouse reachable")
