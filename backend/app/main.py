from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_database
from app.api import agents, auth, companies, financials, kpis, reports, initiatives, variances, drivers, emails, orchestrator, portfolio, scenarios
from app.websocket.manager import router as websocket_router
from app.tasks.scheduler import start_scheduler
from app.config import settings
from app.logger import logger

app = FastAPI(
    title="Autonomous FP&A Platform",
    version="1.0"
)

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if settings.API_KEY:
        if request.url.path in {"/docs", "/openapi.json"}:
            return await call_next(request)
        if request.headers.get("X-API-Key") != settings.API_KEY:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)

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
        start_scheduler()
