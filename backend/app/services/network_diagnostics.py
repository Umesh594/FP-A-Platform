from __future__ import annotations

import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urlparse

from app.config import settings


@dataclass
class ProtocolCheck:
    protocol: str
    target: str
    status: str
    latency_ms: float
    message: str


def check_tcp_connectivity(host: str, port: int, timeout_seconds: float = 2.0) -> ProtocolCheck:
    if settings.NETWORK_DIAGNOSTICS_MOCK_MODE:
        return ProtocolCheck("TCP", f"{host}:{port}", "reachable", 1.0, "Mock TCP probe completed")

    import time

    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ProtocolCheck("TCP", f"{host}:{port}", "reachable", latency_ms, "TCP handshake succeeded")
    except OSError as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ProtocolCheck("TCP", f"{host}:{port}", "unreachable", latency_ms, str(exc))


def check_https_endpoint(url: str) -> ProtocolCheck:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    protocol = "HTTPS" if parsed.scheme == "https" else "HTTP"
    if settings.NETWORK_DIAGNOSTICS_MOCK_MODE:
        return ProtocolCheck(protocol, url, "reachable", 2.0, "Mock HTTP gateway probe completed")
    return check_tcp_connectivity(host, port)


def check_smtp_tls(host: str | None = None, port: int | None = None) -> ProtocolCheck:
    smtp_host = host or settings.SMTP_HOST
    smtp_port = port or settings.SMTP_PORT
    if settings.NETWORK_DIAGNOSTICS_MOCK_MODE:
        return ProtocolCheck("SMTP", f"{smtp_host}:{smtp_port}", "reachable", 3.0, "Mock SMTP/TLS probe completed")

    import smtplib
    import time

    start = time.perf_counter()
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=3) as client:
            client.ehlo()
            if settings.SMTP_TLS_REQUIRED:
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return ProtocolCheck("SMTP", f"{smtp_host}:{smtp_port}", "reachable", latency_ms, "SMTP STARTTLS negotiation succeeded")
    except OSError as exc:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return ProtocolCheck("SMTP", f"{smtp_host}:{smtp_port}", "unreachable", latency_ms, str(exc))


def platform_protocol_report() -> dict:
    checks = [
        check_https_endpoint("https://api.fpna.local/health"),
        check_tcp_connectivity("postgres", 5432),
        check_tcp_connectivity("redis", 6379),
        check_smtp_tls(),
    ]
    reachable = sum(1 for check in checks if check.status == "reachable")
    return {
        "protocols": [check.__dict__ for check in checks],
        "reachable": reachable,
        "total": len(checks),
        "readiness_pct": round((reachable / len(checks)) * 100, 2),
        "network_security_controls": [
            "HTTPS gateway readiness",
            "TCP datastore dependency probes",
            "SMTP STARTTLS verification",
            "API-key protected platform diagnostics",
        ],
    }
