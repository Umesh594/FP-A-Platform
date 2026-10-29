import hashlib
import re
from typing import Any

from app.logger import logger
from app.observability.splunk_hec import emit_to_splunk


EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{7,}\d")
SECRET_KEYS = {"api_key", "authorization", "password", "secret", "token"}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()[:16]


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        value = EMAIL_PATTERN.sub("[email]", value)
        value = PHONE_PATTERN.sub("[phone]", value)
        return value[:160]
    if isinstance(value, dict):
        return redact_payload(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value[:25]]
    return value


def redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        if key.lower().replace("-", "_") in SECRET_KEYS:
            redacted[key] = "[secret]"
        else:
            redacted[key] = redact_value(value)
    return redacted


def audit_event(event_name: str, **fields: Any) -> None:
    safe_fields = redact_payload(fields)
    logger.info("audit_event=%s fields=%s", event_name, safe_fields)
    emit_to_splunk(event_name, safe_fields)
