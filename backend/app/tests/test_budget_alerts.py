"""Tests for D-06: budget 80% alert via Telegram."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.budget_service import check_and_alert

_USER_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()
_MONTH = "2026-06"


def _make_budget(limit_cents: int, alert_sent: bool = False):
    b = MagicMock()
    b.limit_cents = limit_cents
    b.alert_80_sent = alert_sent
    return b


def _make_category(type_: str = "expense"):
    c = MagicMock()
    c.name = "Food"
    c.type = type_
    return c


def _make_db(budget, category, actual_cents: int):
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    call_count = 0

    async def execute_side_effect(_query):
        nonlocal call_count
        call_count += 1
        result = MagicMock()
        if call_count == 1:
            result.scalar_one_or_none.return_value = budget
        elif call_count == 2:
            result.scalar_one_or_none.return_value = category
        else:
            result.scalar_one_or_none.return_value = actual_cents
        return result

    db.execute = AsyncMock(side_effect=execute_side_effect)
    return db


@pytest.mark.asyncio
async def test_alert_sent_when_over_80_pct():
    budget = _make_budget(limit_cents=10000)
    cat = _make_category()
    db = _make_db(budget, cat, actual_cents=8500)

    with patch("app.services.budget_service.send_message", new=AsyncMock()) as mock_send:
        await check_and_alert(
            user_id=_USER_ID,
            telegram_id=12345,
            category_id=_CAT_ID,
            month=_MONTH,
            db=db,
        )
        mock_send.assert_called_once()
        assert "Food" in mock_send.call_args[0][1]

    assert budget.alert_80_sent is True
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_no_alert_when_under_80_pct():
    budget = _make_budget(limit_cents=10000)
    cat = _make_category()
    db = _make_db(budget, cat, actual_cents=7999)

    with patch("app.services.budget_service.send_message", new=AsyncMock()) as mock_send:
        await check_and_alert(
            user_id=_USER_ID,
            telegram_id=12345,
            category_id=_CAT_ID,
            month=_MONTH,
            db=db,
        )
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_no_alert_without_telegram_id():
    db = AsyncMock()
    with patch("app.services.budget_service.send_message", new=AsyncMock()) as mock_send:
        await check_and_alert(
            user_id=_USER_ID,
            telegram_id=None,
            category_id=_CAT_ID,
            month=_MONTH,
            db=db,
        )
        mock_send.assert_not_called()
    db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_no_duplicate_alert_if_already_sent():
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # budget not found (alert_80_sent=True filtered)
    db.execute = AsyncMock(return_value=result)

    with patch("app.services.budget_service.send_message", new=AsyncMock()) as mock_send:
        await check_and_alert(
            user_id=_USER_ID,
            telegram_id=12345,
            category_id=_CAT_ID,
            month=_MONTH,
            db=db,
        )
        mock_send.assert_not_called()
