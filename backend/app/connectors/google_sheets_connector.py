from app.connectors.base import BaseConnector, ConnectorResult


class GoogleSheetsConnector(BaseConnector):
    source_type = "google_sheets"

    def test_connection(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "simulated", 0, "Google Sheets finance planning connector simulated")
