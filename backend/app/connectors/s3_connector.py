from app.connectors.base import BaseConnector, ConnectorResult


class S3Connector(BaseConnector):
    source_type = "s3"

    def test_connection(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "simulated", 0, "S3-compatible board reporting bucket simulated")
