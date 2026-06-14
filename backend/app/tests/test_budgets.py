"""Tests for D-04: budgets CRUD + analytics/budget"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()
_BUDGET_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "d04@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_budget():
    b = MagicMock()
    b.id = _BUDGET_ID
    b.user_id = _USER_ID
    b.category_id = _CAT_ID
    b.month = "2026-06"
    b.limit_cents = 50000
    b.updated_at = datetime.now(timezone.utc)
    return b


def _make_category():
    c = MagicMock()
    c.id = _CAT_ID
    c.user_id = _USER_ID
    c.name = "Groceries"
    c.color = "#E52B50"
    c.type = "expense"
    return c


def _override(app, user, db):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


@pytest.mark.asyncio
async def test_list_budgets_happy():
    from app.main import app

    budget = _make_budget()
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalars.return_value.all.return_value = [budget]
    db.execute = AsyncMock(return_value=scalar_result)
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/budgets", params={"month": "2026-06"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_budgets_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/budgets", params={"month": "2026-06"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upsert_budget_happy():
    from app.main import app

    budget = _make_budget()
    cat = _make_category()
    db = AsyncMock()
    db.get = AsyncMock(return_value=cat)
    execute_result = MagicMock()
    execute_result.fetchone.return_value = (budget,)
    db.execute = AsyncMock(return_value=execute_result)
    db.commit = AsyncMock()
    _override(app, _make_user(), db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post("/budgets", json={
            "category_id": str(_CAT_ID),
            "month": "2026-06",
            "limit_cents": 50000,
        })

    app.dependency_overrides.clear()
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_budget_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete(f"/budgets/{_BUDGET_ID}")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_budget_bars_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/analytics/budget", params={"month": "2026-06"})

    assert resp.status_code == 401
