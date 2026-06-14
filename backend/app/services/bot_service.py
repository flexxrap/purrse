import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.services import analytics_service, telegram_service

logger = logging.getLogger(__name__)


def _fmt(cents: int, currency: str) -> str:
    return f"{cents / 100:.2f} {currency}"


async def handle_update(update: dict, db: AsyncSession) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return
    text: str = message.get("text", "")
    telegram_id: int | None = message.get("from", {}).get("id")
    if not telegram_id or not text.startswith("/"):
        return

    cmd = text.split()[0].split("@")[0]
    if cmd == "/start":
        await _cmd_start(telegram_id)
    elif cmd == "/stats":
        await _cmd_stats(telegram_id, db)
    elif cmd == "/help":
        await _cmd_help(telegram_id)


async def _cmd_start(telegram_id: int) -> None:
    text = (
        "👋 Привет! Я — purrse, умный трекер финансов.\n\n"
        "Отслеживай доходы и расходы по категориям, "
        "ставь цели и контролируй бюджет.\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение 👇"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "💰 Открыть purrse", "web_app": {"url": settings.FRONTEND_URL}}
        ]]
    }
    await telegram_service.send_message(telegram_id, text, reply_markup=keyboard)


async def _cmd_stats(telegram_id: int, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        await telegram_service.send_message(
            telegram_id,
            "❓ Аккаунт не найден.\n"
            "Открой приложение и войди через Telegram, чтобы привязать аккаунт.",
        )
        return

    now = datetime.now(timezone.utc)
    data = await analytics_service.summary(user.id, now.year, now.month, db)
    currency = user.currency
    income = _fmt(data["income_cents"], currency)
    expense = _fmt(data["expense_cents"], currency)
    balance_cents = data["balance_cents"]
    sign = "+" if balance_cents >= 0 else ""
    balance = sign + _fmt(abs(balance_cents), currency)
    month_str = now.strftime("%B %Y")

    text = (
        f"📊 *{month_str}*\n\n"
        f"⬆️ Доходы: `{income}`\n"
        f"⬇️ Расходы: `{expense}`\n"
        f"💰 Баланс: `{balance}`"
    )
    await telegram_service.send_message(telegram_id, text, parse_mode="Markdown")


async def _cmd_help(telegram_id: int) -> None:
    text = (
        "🐱 *purrse — команды*\n\n"
        "/start — приветствие и кнопка открыть приложение\n"
        "/stats — статистика за текущий месяц\n"
        "/help — эта справка\n\n"
        "Всё остальное доступно в приложении 💰"
    )
    await telegram_service.send_message(telegram_id, text, parse_mode="Markdown")


async def send_monthly_summary(db: AsyncSession) -> None:
    """Send previous month summary to all Telegram users. Runs on the 1st of each month."""
    now = datetime.now(timezone.utc)
    year, month = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    month_str = datetime(year, month, 1).strftime("%B %Y")

    result = await db.execute(select(User).where(User.telegram_id.isnot(None)))
    users = result.scalars().all()

    for user in users:
        try:
            data = await analytics_service.summary(user.id, year, month, db)
            currency = user.currency
            income = _fmt(data["income_cents"], currency)
            expense = _fmt(data["expense_cents"], currency)
            balance_cents = data["balance_cents"]
            sign = "+" if balance_cents >= 0 else ""
            balance = sign + _fmt(abs(balance_cents), currency)

            text = (
                f"📅 *Итоги {month_str}*\n\n"
                f"⬆️ Доходы: `{income}`\n"
                f"⬇️ Расходы: `{expense}`\n"
                f"💰 Баланс: `{balance}`\n\n"
                "Подробнее — в приложении 👇"
            )
            keyboard = {
                "inline_keyboard": [[
                    {"text": "📊 Открыть purrse", "web_app": {"url": settings.FRONTEND_URL}}
                ]]
            }
            await telegram_service.send_message(
                user.telegram_id, text, parse_mode="Markdown", reply_markup=keyboard
            )
        except Exception:
            logger.exception("Failed monthly summary for user %s", user.id)
