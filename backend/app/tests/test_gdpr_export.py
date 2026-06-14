"""Tests for S-11: GET /user/me/export (GDPR data export)."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "test@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_db_with_empty_results():
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result_mock)
    return db


@pytest.mark.asyncio
async def test_export_happy():
    from app.dependencies import get_current_user, get_db
    from app.main import app

    user = _make_user()
    db = _make_db_with_empty_results()

    async def override_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/user/me/export")

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.headers["content-disposition"] == "attachment; filename=budget-data-export.json"
    body = resp.json()
    assert "user" in body
    assert "transactions" in body
    assert "categories" in body
    assert "goals" in body
    assert "budgets" in body
    assert body["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_export_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.get("/user/me/export")

    assert resp.status_code == 401
