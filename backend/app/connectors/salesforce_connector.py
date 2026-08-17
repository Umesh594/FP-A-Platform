from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import settings
from app.connectors.base import BaseConnector, ConnectorResult


class SalesforceIntegrationError(RuntimeError):
    """Raised when Salesforce data exchange fails after retries."""


@dataclass(frozen=True)
class SalesforceConfig:
    base_url: str
    client_id: str
    client_secret: str
    username: str
    password: str
    security_token: str
    api_version: str = "v60.0"
    timeout_seconds: int = 15
    mock_mode: bool = True

    @classmethod
    def from_settings(cls) -> "SalesforceConfig":
        return cls(
            base_url=settings.SALESFORCE_BASE_URL.rstrip("/"),
            client_id=settings.SALESFORCE_CLIENT_ID,
            client_secret=settings.SALESFORCE_CLIENT_SECRET,
            username=settings.SALESFORCE_USERNAME,
            password=settings.SALESFORCE_PASSWORD,
            security_token=settings.SALESFORCE_SECURITY_TOKEN,
            api_version=settings.SALESFORCE_API_VERSION,
            timeout_seconds=settings.SALESFORCE_TIMEOUT_SECONDS,
            mock_mode=settings.SALESFORCE_MOCK_MODE,
        )

    def validate(self) -> None:
        if self.mock_mode:
            return
        missing = [
            name
            for name, value in {
                "SALESFORCE_BASE_URL": self.base_url,
                "SALESFORCE_CLIENT_ID": self.client_id,
                "SALESFORCE_CLIENT_SECRET": self.client_secret,
                "SALESFORCE_USERNAME": self.username,
                "SALESFORCE_PASSWORD": self.password,
            }.items()
            if not value
        ]
        if missing:
            raise SalesforceIntegrationError(f"Missing Salesforce settings: {', '.join(missing)}")

    def safe_summary(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "api_version": self.api_version,
            "mock_mode": self.mock_mode,
            "username_configured": bool(self.username),
            "client_id_configured": bool(self.client_id),
            "credentials_redacted": True,
        }


class SalesforceConnector(BaseConnector):
    source_type = "salesforce"

    ACCOUNT_FIELDS = ["Id", "Name", "Industry", "AnnualRevenue", "OwnerId", "LastModifiedDate"]
    OPPORTUNITY_FIELDS = [
        "Id",
        "AccountId",
        "Name",
        "StageName",
        "Amount",
        "Probability",
        "CloseDate",
        "ForecastCategoryName",
        "LastModifiedDate",
    ]

    def __init__(self, name: str = "salesforce-crm", config: SalesforceConfig | None = None):
        super().__init__(name)
        self.config = config or SalesforceConfig.from_settings()
        self._access_token: str | None = None
        self._instance_url: str | None = None

    def test_connection(self) -> ConnectorResult:
        self.config.validate()
        if self.config.mock_mode:
            return ConnectorResult(
                self.name,
                self.source_type,
                "simulated",
                0,
                "Salesforce connector ready in mock mode; no secrets used",
            )
        self._authenticate()
        return ConnectorResult(self.name, self.source_type, "connected", 0, "Salesforce OAuth connection succeeded")

    def sync(self) -> ConnectorResult:
        payload = self.build_financial_pipeline_payload()
        rows_available = payload["summary"]["open_opportunity_count"] + payload["summary"]["account_count"]
        return ConnectorResult(
            self.name,
            self.source_type,
            "synced",
            rows_available,
            "Salesforce accounts and opportunity pipeline synced into FP&A metrics",
        )

    def build_financial_pipeline_payload(
        self,
        include_accounts: bool = True,
        include_opportunities: bool = True,
    ) -> dict[str, Any]:
        accounts = self.fetch_accounts() if include_accounts else []
        opportunities = [
            self.normalize_opportunity(row)
            for row in (self.fetch_opportunities() if include_opportunities else [])
        ]
        open_opportunities = [row for row in opportunities if row["stage_name"].lower() not in {"closed won", "closed lost"}]
        closed_won = [row for row in opportunities if row["stage_name"].lower() == "closed won"]

        return {
            "source": self.source_type,
            "synced_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "config": self.config.safe_summary(),
            "accounts": accounts,
            "opportunities": opportunities,
            "summary": {
                "account_count": len(accounts),
                "open_opportunity_count": len(open_opportunities),
                "total_pipeline_amount": round(sum(row["amount"] for row in open_opportunities), 2),
                "weighted_pipeline_amount": round(sum(row["weighted_amount"] for row in open_opportunities), 2),
                "closed_won_amount": round(sum(row["amount"] for row in closed_won), 2),
            },
        }

    def fetch_accounts(self) -> list[dict[str, Any]]:
        if self.config.mock_mode:
            return self._mock_accounts()
        query = f"SELECT {', '.join(self.ACCOUNT_FIELDS)} FROM Account WHERE LastModifiedDate = LAST_N_DAYS:90"
        return self._query_all(query)

    def fetch_opportunities(self) -> list[dict[str, Any]]:
        if self.config.mock_mode:
            return self._mock_opportunities()
        query = (
            f"SELECT {', '.join(self.OPPORTUNITY_FIELDS)} FROM Opportunity "
            "WHERE CloseDate = THIS_FISCAL_YEAR OR LastModifiedDate = LAST_N_DAYS:90"
        )
        return self._query_all(query)

    def normalize_opportunity(self, row: dict[str, Any]) -> dict[str, Any]:
        amount = float(row.get("Amount") or row.get("amount") or 0)
        probability = float(row.get("Probability") or row.get("probability") or 0)
        close_date = row.get("CloseDate") or row.get("close_date")
        return {
            "opportunity_id": row.get("Id") or row.get("opportunity_id"),
            "account_id": row.get("AccountId") or row.get("account_id"),
            "name": row.get("Name") or row.get("name") or "",
            "stage_name": row.get("StageName") or row.get("stage_name") or "Unknown",
            "amount": round(amount, 2),
            "probability": round(probability, 2),
            "weighted_amount": round(amount * probability / 100, 2),
            "close_date": close_date,
            "fiscal_quarter": self._fiscal_quarter(close_date),
            "forecast_category": row.get("ForecastCategoryName") or row.get("forecast_category") or "Pipeline",
            "last_modified": row.get("LastModifiedDate") or row.get("last_modified"),
        }

    def _authenticate(self) -> None:
        if self._access_token:
            return
        self.config.validate()
        token_url = f"{self.config.base_url}/services/oauth2/token"
        form = urlencode(
            {
                "grant_type": "password",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": f"{self.config.password}{self.config.security_token}",
            }
        ).encode("utf-8")
        response = self._request(
            token_url,
            method="POST",
            body=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=False,
        )
        self._access_token = response["access_token"]
        self._instance_url = response.get("instance_url", self.config.base_url).rstrip("/")

    def _query_all(self, soql: str) -> list[dict[str, Any]]:
        self._authenticate()
        records: list[dict[str, Any]] = []
        url = f"{self._instance_url}/services/data/{self.config.api_version}/query?{urlencode({'q': soql})}"
        while url:
            response = self._request(url)
            records.extend(response.get("records", []))
            next_url = response.get("nextRecordsUrl")
            url = f"{self._instance_url}{next_url}" if next_url else ""
        return [{key: value for key, value in row.items() if key != "attributes"} for row in records]

    def _request(
        self,
        url: str,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = True,
        retries: int = 2,
    ) -> dict[str, Any]:
        request_headers = {"Accept": "application/json", **(headers or {})}
        if auth:
            request_headers["Authorization"] = f"Bearer {self._access_token}"

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                request = Request(url, data=body, headers=request_headers, method=method)
                with urlopen(request, timeout=self.config.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code < 500 and exc.code != 429:
                    raise SalesforceIntegrationError(f"Salesforce request failed with HTTP {exc.code}") from exc
                last_error = exc
            except (TimeoutError, URLError) as exc:
                last_error = exc
            time.sleep(0.25 * (attempt + 1))
        raise SalesforceIntegrationError("Salesforce request failed after retries") from last_error

    def _fiscal_quarter(self, value: str | None) -> str | None:
        if not value:
            return None
        parsed = date.fromisoformat(value[:10])
        quarter = ((parsed.month - 1) // 3) + 1
        return f"FY{parsed.year}Q{quarter}"

    def _mock_accounts(self) -> list[dict[str, Any]]:
        return [
            {"Id": "001-cloudcrm", "Name": "CloudCRM Inc", "Industry": "SaaS", "AnnualRevenue": 42000000},
            {"Id": "001-fintech", "Name": "Fintech Payments", "Industry": "FinTech", "AnnualRevenue": 61000000},
            {"Id": "001-health", "Name": "HealthcareTech", "Industry": "Healthcare", "AnnualRevenue": 38000000},
        ]

    def _mock_opportunities(self) -> list[dict[str, Any]]:
        return [
            {
                "Id": "006-expansion-1",
                "AccountId": "001-cloudcrm",
                "Name": "CloudCRM Enterprise Expansion",
                "StageName": "Negotiation",
                "Amount": 1250000,
                "Probability": 70,
                "CloseDate": "2026-09-30",
                "ForecastCategoryName": "Commit",
                "LastModifiedDate": "2026-08-01T10:30:00Z",
            },
            {
                "Id": "006-renewal-2",
                "AccountId": "001-fintech",
                "Name": "Fintech Payments Renewal",
                "StageName": "Proposal",
                "Amount": 840000,
                "Probability": 55,
                "CloseDate": "2026-10-15",
                "ForecastCategoryName": "Best Case",
                "LastModifiedDate": "2026-08-03T08:15:00Z",
            },
            {
                "Id": "006-won-3",
                "AccountId": "001-health",
                "Name": "HealthcareTech Analytics Add-on",
                "StageName": "Closed Won",
                "Amount": 460000,
                "Probability": 100,
                "CloseDate": "2026-07-31",
                "ForecastCategoryName": "Closed",
                "LastModifiedDate": "2026-07-31T18:45:00Z",
            },
        ]
