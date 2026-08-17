import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.connectors.salesforce_connector import SalesforceConfig, SalesforceConnector, SalesforceIntegrationError


def test_salesforce_config_redacts_secrets():
    config = SalesforceConfig(
        base_url="https://example.my.salesforce.com",
        client_id="client",
        client_secret="secret",
        username="user@example.com",
        password="password",
        security_token="token",
        mock_mode=True,
    )

    summary = config.safe_summary()

    assert summary["client_id_configured"] is True
    assert summary["username_configured"] is True
    assert summary["credentials_redacted"] is True
    assert "secret" not in str(summary)
    assert "password" not in str(summary)


def test_salesforce_live_mode_requires_credentials():
    config = SalesforceConfig(
        base_url="",
        client_id="",
        client_secret="",
        username="",
        password="",
        security_token="",
        mock_mode=False,
    )

    try:
        config.validate()
    except SalesforceIntegrationError as exc:
        assert "SALESFORCE_BASE_URL" in str(exc)
        assert "SALESFORCE_CLIENT_ID" in str(exc)
    else:
        raise AssertionError("Expected missing Salesforce settings to fail validation")


def test_salesforce_mock_pipeline_calculates_weighted_revenue():
    connector = SalesforceConnector(
        config=SalesforceConfig(
            base_url="https://example.my.salesforce.com",
            client_id="",
            client_secret="",
            username="",
            password="",
            security_token="",
            mock_mode=True,
        )
    )

    payload = connector.build_financial_pipeline_payload()

    assert payload["summary"]["account_count"] == 3
    assert payload["summary"]["open_opportunity_count"] == 2
    assert payload["summary"]["total_pipeline_amount"] == 2090000
    assert payload["summary"]["weighted_pipeline_amount"] == 1337000
    assert payload["summary"]["closed_won_amount"] == 460000
    assert payload["opportunities"][0]["fiscal_quarter"] == "FY2026Q3"


def test_salesforce_connector_sync_reports_rows():
    connector = SalesforceConnector(
        config=SalesforceConfig(
            base_url="https://example.my.salesforce.com",
            client_id="",
            client_secret="",
            username="",
            password="",
            security_token="",
            mock_mode=True,
        )
    )

    result = connector.sync()

    assert result.source_type == "salesforce"
    assert result.status == "synced"
    assert result.rows_available == 5
