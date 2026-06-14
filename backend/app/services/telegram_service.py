import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_BASE = "https://api.telegram.org"


async def send_message(telegram_id: int, text: str) -> None:
    url = f"{_TELEGRAM_BASE}/bot{settings.BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json={"chat_id": telegram_id, "text": text})
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("Telegram notification to %d failed: %s", telegram_id, exc)
