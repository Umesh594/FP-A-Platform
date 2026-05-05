from app.connectors.base import BaseConnector, ConnectorResult


class CsvConnector(BaseConnector):
    source_type = "csv"

    def sync(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "synced", 216, "Seeded CSV financial files synced")
