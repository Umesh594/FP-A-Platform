from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.connectors.base import BaseConnector, ConnectorResult


class WorkdayIntegrationError(RuntimeError):
    """Raised when the configured Workday workforce feed cannot be read safely."""


@dataclass(frozen=True)
class WorkdayConfig:
    base_url: str
    bearer_token: str
    timeout_seconds: int = 15
    mock_mode: bool = True

    @classmethod
    def from_settings(cls) -> "WorkdayConfig":
        return cls(
            base_url=settings.WORKDAY_BASE_URL.rstrip("/"),
            bearer_token=settings.WORKDAY_BEARER_TOKEN,
            timeout_seconds=settings.WORKDAY_TIMEOUT_SECONDS,
            mock_mode=settings.WORKDAY_MOCK_MODE,
        )

    def validate(self) -> None:
        if not self.mock_mode and (not self.base_url or not self.bearer_token):
            raise WorkdayIntegrationError("WORKDAY_BASE_URL and WORKDAY_BEARER_TOKEN are required when mock mode is disabled")

    def safe_summary(self) -> dict[str, Any]:
        return {"base_url": self.base_url, "mock_mode": self.mock_mode, "credentials_redacted": True}


class WorkdayWorkforceConnector(BaseConnector):
    """Imports aggregated department-month workforce data, never individual employee records."""

    source_type = "workday"

    def __init__(self, name: str = "workday-workforce", config: WorkdayConfig | None = None):
        super().__init__(name)
        self.config = config or WorkdayConfig.from_settings()

    def test_connection(self) -> ConnectorResult:
        self.config.validate()
        if self.config.mock_mode:
            return ConnectorResult(self.name, self.source_type, "simulated", 4, "Workday workforce adapter ready in mock mode")
        self._request("/health")
        return ConnectorResult(self.name, self.source_type, "connected", 0, "Workday workforce adapter connection succeeded")

    def fetch_department_months(self) -> list[dict[str, Any]]:
        self.config.validate()
        rows = self._mock_rows() if self.config.mock_mode else self._request("/workforce/department-months").get("rows", [])
        normalized = [self._normalize(row) for row in rows]
        if any(row["actual_headcount"] < 0 or row["actual_monthly_cost"] < 0 for row in normalized):
            raise WorkdayIntegrationError("Workday feed contains invalid negative workforce values")
        return normalized

    def sync(self) -> ConnectorResult:
        return ConnectorResult(self.name, self.source_type, "synced", len(self.fetch_department_months()), "Workday department-month workforce data fetched")

    def _request(self, path: str) -> dict[str, Any]:
        request = Request(
            f"{self.config.base_url}{path}",
            headers={"Accept": "application/json", "Authorization": f"Bearer {self.config.bearer_token}"},
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise WorkdayIntegrationError(f"Workday request failed with HTTP {exc.code}") from exc
        except (TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise WorkdayIntegrationError("Workday request failed or returned invalid JSON") from exc

    @staticmethod
    def _normalize(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "department": str(row["department"]).strip(),
            "period": date.fromisoformat(str(row["period"])[:10]),
            "actual_headcount": int(row["actual_headcount"]),
            "actual_monthly_cost": round(float(row["actual_monthly_cost"]), 2),
            "source": "workday",
            "quality_status": "valid",
        }

    @staticmethod
    def _mock_rows() -> list[dict[str, Any]]:
        return [
            {"department": "Engineering", "period": "2026-11-01", "actual_headcount": 42, "actual_monthly_cost": 504000},
            {"department": "Sales", "period": "2026-11-01", "actual_headcount": 28, "actual_monthly_cost": 252000},
            {"department": "People", "period": "2026-11-01", "actual_headcount": 8, "actual_monthly_cost": 80000},
            {"department": "Finance", "period": "2026-11-01", "actual_headcount": 12, "actual_monthly_cost": 144000},
        ]
