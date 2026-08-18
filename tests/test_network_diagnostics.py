import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.services.network_diagnostics import platform_protocol_report


def test_platform_protocol_report_covers_http_tcp_smtp():
    report = platform_protocol_report()
    protocols = {row["protocol"] for row in report["protocols"]}

    assert {"HTTPS", "TCP", "SMTP"}.issubset(protocols)
    assert report["total"] == 4
    assert report["readiness_pct"] == 100.0
    assert "SMTP STARTTLS verification" in report["network_security_controls"]
