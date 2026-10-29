from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings
from app.logger import logger


def build_hec_event(event_name: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "time": datetime.now(timezone.utc).timestamp(),
        "host": settings.APP_NAME,
        "source": "fpa-api",
        "sourcetype": "_json",
        "index": settings.SPLUNK_HEC_INDEX,
        "event": {"event_name": event_name, **fields},
    }


def emit_to_splunk(event_name: str, fields: dict[str, Any]) -> bool:
    """Best-effort HEC delivery; observability must never break a business request."""
    if not settings.SPLUNK_HEC_URL or not settings.SPLUNK_HEC_TOKEN:
        return False
    try:
        response = httpx.post(
            settings.SPLUNK_HEC_URL.rstrip("/") + "/services/collector/event",
            json=build_hec_event(event_name, fields),
            headers={"Authorization": f"Splunk {settings.SPLUNK_HEC_TOKEN}"},
            timeout=1.0,
        )
        response.raise_for_status()
        return True
    except httpx.HTTPError as exc:
        logger.warning("splunk_hec_delivery_failed event=%s error=%s", event_name, type(exc).__name__)
        return False
