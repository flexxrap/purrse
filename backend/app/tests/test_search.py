"""
Tests for T-07: full-text search on transaction notes (?search=).
Uses mock DB — no real Postgres needed.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "t07@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_tx(note="coffee shop"):
    tx = MagicMock()
    tx.id = uuid.uuid4()
    tx.user_id = _USER_ID
    tx.account_id = uuid.uuid4()
    tx.category_id = uuid.uuid4()
    tx.amount_cents = 500
    tx.note = note
    tx.tx_date = date.today()
    tx.created_at = datetime.now(timezone.utc)
    tx.updated_at = datetime.now(timezone.utc)
    tx.deleted_at = None
    return tx


def _override(app, user, rows):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalars.return_value.all.return_value = rows
    db.execute = AsyncMock(return_value=scalar_result)

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


@pytest.mark.asyncio
async def test_search_happy_path():
    from app.main import app

    tx = _make_tx(note="coffee shop downtown")
    _override(app, _make_user(), [tx])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/transactions", params={"search": "coffee"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_search_too_short_rejected():
    from app.main import app

    _override(app, _make_user(), [])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/transactions", params={"search": "ab"})

    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/transactions", params={"search": "coffee"})

    assert resp.status_code == 401
