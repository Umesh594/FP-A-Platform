from app.connectors.base import BaseConnector, ConnectorResult


class MockErpConnector(BaseConnector):
    source_type = "mock_erp"

    def sync(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "synced", 64, "Mock ERP ledger sync completed")
