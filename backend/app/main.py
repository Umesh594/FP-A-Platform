import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import init_database
from app.api import agents, auth, companies, financials, integrations, kpis, reports, initiatives, variances, drivers, emails, orchestrator, platform, portfolio, scenarios, powerbi
from app.websocket.manager import router as websocket_router
from app.config import settings
from app.logger import logger
from app.services.privacy import audit_event

app = FastAPI(
    title="Autonomous FP&A Platform",
    version="1.0"
)

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    start = time.perf_counter()
    if settings.API_KEY:
        if request.url.path in {"/docs", "/openapi.json"}:
            return await call_next(request)
        if request.headers.get("X-API-Key") != settings.API_KEY:
            audit_event("api_key_rejected", path=request.url.path, method=request.method, request_id=request_id)
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"}, headers={"X-Request-ID": request_id})
    response = await call_next(request)
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(latency_ms)
    audit_event(
        "request_completed",
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        latency_ms=latency_ms,
        request_id=request_id,
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"]
)

app.include_router(companies.router)
app.include_router(financials.router)
app.include_router(kpis.router)
app.include_router(reports.router)
app.include_router(initiatives.router)
app.include_router(variances.router)
app.include_router(drivers.router)
app.include_router(emails.router)
app.include_router(websocket_router)
app.include_router(scenarios.router)
app.include_router(orchestrator.router)
app.include_router(portfolio.router)
app.include_router(agents.router)
app.include_router(auth.router)
app.include_router(platform.router)
app.include_router(integrations.router)
app.include_router(powerbi.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.on_event("startup")
async def startup():
    try:
        init_database()
    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")
        raise
    if settings.ENABLE_API_SCHEDULER:
        from app.tasks.scheduler import start_scheduler

        start_scheduler()
