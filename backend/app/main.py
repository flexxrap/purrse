import logging
from contextlib import asynccontextmanager

import sentry_sdk
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import AsyncSessionLocal
from app.limiter import limiter
from app.services import recurring_service

logger = logging.getLogger(__name__)

_dsn = settings.SENTRY_DSN
if _dsn and _dsn.startswith("https://") and "/" in _dsn.split("@")[-1]:
    sentry_sdk.init(dsn=_dsn, traces_sample_rate=0.2)

scheduler = AsyncIOScheduler()


async def _run_recurring():
    async with AsyncSessionLocal() as db:
        await recurring_service.process_due(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _run_recurring()
    scheduler.add_job(_run_recurring, "cron", hour=0, minute=5)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Budget App API", version="0.1.0", lifespan=lifespan)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://telegram.org; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'"
    )
    return response


from app.routers import (  # noqa: E402
    analytics,
    auth,
    budgets,
    categories,
    goals,
    recurring,
    transactions,
    user,
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(analytics.router)
app.include_router(budgets.router)
app.include_router(recurring.router)


@app.get("/health", tags=["health"])
async def health():
    return JSONResponse({"status": "ok"})
