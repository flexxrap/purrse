import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_BASE = "https://api.telegram.org"


async def send_message(
    telegram_id: int,
    text: str,
    parse_mode: str | None = None,
    reply_markup: dict | None = None,
) -> None:
    url = f"{_TELEGRAM_BASE}/bot{settings.BOT_TOKEN}/sendMessage"
    payload: dict = {"chat_id": telegram_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
    except Exception as exc:
        logger.warning("Telegram notification to %d failed: %s", telegram_id, exc)
