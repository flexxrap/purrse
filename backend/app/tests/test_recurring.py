"""Tests for T-10: recurring transactions CRUD"""
import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_RT_ID = uuid.uuid4()
_ACCOUNT_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "t10@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_rt():
    rt = MagicMock()
    rt.id = _RT_ID
    rt.user_id = _USER_ID
    rt.account_id = _ACCOUNT_ID
    rt.category_id = None
    rt.amount_cents = 5000
    rt.note = "Monthly rent"
    rt.frequency = "monthly"
    rt.next_date = date(2026, 7, 1)
    rt.is_active = True
    rt.created_at = datetime.now(timezone.utc)
    rt.updated_at = datetime.now(timezone.utc)
    return rt


def _override(app, user, db):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


@pytest.mark.asyncio
async def test_list_recurring_happy():
    from app.main import app

    rt = _make_rt()
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [rt]
    db.execute = AsyncMock(return_value=result)
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/recurring")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_recurring_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/recurring")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_recurring_happy():
    from app.main import app

    rt = _make_rt()
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    async def fake_refresh(obj):
        obj.id = rt.id
        obj.user_id = rt.user_id
        obj.account_id = rt.account_id
        obj.category_id = rt.category_id
        obj.amount_cents = rt.amount_cents
        obj.note = rt.note
        obj.frequency = rt.frequency
        obj.next_date = rt.next_date
        obj.is_active = rt.is_active
        obj.created_at = rt.created_at
        obj.updated_at = rt.updated_at

    db.refresh = AsyncMock(side_effect=fake_refresh)
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post("/recurring", json={
            "account_id": str(_ACCOUNT_ID),
            "amount_cents": 5000,
            "frequency": "monthly",
            "start_date": "2026-07-01",
        })

    app.dependency_overrides.clear()
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_recurring_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post("/recurring", json={
            "amount_cents": 5000,
            "frequency": "monthly",
            "start_date": "2026-07-01",
        })

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_delete_recurring_happy():
    from app.main import app

    rt = _make_rt()
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = rt
    db.execute = AsyncMock(return_value=result)
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete(f"/recurring/{_RT_ID}")

    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_recurring_not_found():
    from app.main import app

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=result)
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete(f"/recurring/{_RT_ID}")

    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_recurring_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete(f"/recurring/{_RT_ID}")

    assert resp.status_code == 401
