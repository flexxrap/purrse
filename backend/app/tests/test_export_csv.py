"""Tests for T-09: GET /transactions/export/csv"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "t09@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_row(note="lunch"):
    r = MagicMock()
    r.tx_date = date(2026, 6, 1)
    r.amount_cents = 1500
    r.note = note
    r.category_name = "Food"
    r.category_type = "expense"
    return r


def _override(app, user, rows):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows
    db.execute = AsyncMock(return_value=result)

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


@pytest.mark.asyncio
async def test_export_csv_happy():
    from app.main import app

    _override(app, _make_user(), [_make_row()])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/transactions/export/csv")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "attachment" in resp.headers["content-disposition"]
    lines = resp.text.strip().splitlines()
    assert lines[0] == "Date,Category,Type,Amount,Note"
    assert "2026-06-01" in lines[1]
    assert "15.00" in lines[1]


@pytest.mark.asyncio
async def test_export_csv_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/transactions/export/csv")

    assert resp.status_code == 401
