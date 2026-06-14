import hashlib
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.services import bot_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bot", tags=["bot"])

# Stable secret derived from BOT_TOKEN — set as `secret_token` when registering webhook
_WEBHOOK_SECRET = hashlib.sha256(settings.BOT_TOKEN.encode()).hexdigest()


@router.post("/webhook")
async def webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    if x_telegram_bot_api_secret_token != _WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    update = await request.json()
    await bot_service.handle_update(update, db)
    return {"ok": True}
