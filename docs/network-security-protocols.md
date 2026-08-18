# Network Security and Protocol Coverage

The FP&A platform now exposes production-support diagnostics for common SaaS protocols:

- HTTP/HTTPS gateway readiness for API entrypoints.
- TCP dependency probes for PostgreSQL/TimescaleDB and Redis.
- SMTP STARTTLS readiness for report and alert delivery.
- API-key protected diagnostics to avoid exposing dependency health publicly.

Endpoint:

```text
GET /platform/network/protocols
```

The endpoint returns protocol, target, status, latency, readiness percentage, and security-control coverage so support teams can quickly separate application failures from network dependency failures.
