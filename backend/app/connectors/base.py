from dataclasses import dataclass


@dataclass
class ConnectorResult:
    name: str
    source_type: str
    status: str
    rows_available: int
    message: str


class BaseConnector:
    source_type = "base"

    def __init__(self, name: str):
        self.name = name

    def test_connection(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "connected", 0, "Connection test passed")

    def sync(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "synced", 0, "Sync completed")
