import hashlib
import logging
from contextlib import asynccontextmanager

import httpx
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
from app.services import bot_service, recurring_service

logger = logging.getLogger(__name__)

_dsn = settings.SENTRY_DSN
if _dsn and _dsn.startswith("https://") and "/" in _dsn.split("@")[-1]:
    sentry_sdk.init(dsn=_dsn, traces_sample_rate=0.2)

scheduler = AsyncIOScheduler()


async def _run_recurring():
    async with AsyncSessionLocal() as db:
        await recurring_service.process_due(db)


async def _run_monthly_summary():
    async with AsyncSessionLocal() as db:
        await bot_service.send_monthly_summary(db)


async def _register_webhook() -> None:
    if not settings.BACKEND_URL or not settings.BOT_TOKEN:
        return
    webhook_url = f"{settings.BACKEND_URL}/bot/webhook"
    secret = hashlib.sha256(settings.BOT_TOKEN.encode()).hexdigest()
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/setWebhook"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={
                "url": webhook_url,
                "secret_token": secret,
                "allowed_updates": ["message"],
            })
            data = resp.json()
            if data.get("ok"):
                logger.info("Telegram webhook registered: %s", webhook_url)
            else:
                logger.warning("Telegram webhook registration failed: %s", data)
    except Exception as exc:
        logger.warning("Could not register Telegram webhook: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _run_recurring()
    await _register_webhook()
    scheduler.add_job(_run_recurring, "cron", hour=0, minute=5)
    scheduler.add_job(_run_monthly_summary, "cron", day=1, hour=9, minute=0)
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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Return JSON 500 with CORS headers so browsers surface the error
    instead of a generic Network Error (default 500 bypasses CORSMiddleware)."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    headers = {}
    origin = request.headers.get("origin")
    if origin and origin in settings.ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return JSONResponse({"detail": "Internal server error"}, status_code=500, headers=headers)


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
    accounts,
    analytics,
    auth,
    bot,
    budgets,
    categories,
    goals,
    recurring,
    transactions,
    user,
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(goals.router)
app.include_router(analytics.router)
app.include_router(budgets.router)
app.include_router(recurring.router)
app.include_router(bot.router)


@app.get("/health", tags=["health"])
async def health():
    return JSONResponse({"status": "ok"})
