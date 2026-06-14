"""
Tests for A-06 (PATCH /user/me) and A-08 (POST /user/me/password).
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.services.auth_service import hash_password

_USER_ID = uuid.uuid4()
_EMAIL = "alice@example.com"
_PASSWORD = "oldpassword1"
_HASHED_PW = hash_password(_PASSWORD)


def _make_user(email=_EMAIL, currency="USD"):
    u = MagicMock()
    u.id = _USER_ID
    u.email = email
    u.telegram_id = None
    u.currency = currency
    u.password_hash = _HASHED_PW
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


def _db_no_email_conflict():
    """DB mock: email uniqueness check returns None (no conflict)."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=scalar_result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _db_email_conflict():
    """DB mock: email uniqueness check finds an existing user."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=_make_user())
    db.execute = AsyncMock(return_value=scalar_result)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _override_user_and_db(app, user, db):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


# ---------------------------------------------------------------------------
# A-06: PATCH /user/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_currency_happy():
    from app.main import app

    user = _make_user()
    db = _db_no_email_conflict()

    async def refreshed(_):
        user.currency = "EUR"

    db.refresh = AsyncMock(side_effect=refreshed)
    _override_user_and_db(app, user, db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.patch("/user/me", json={"currency": "EUR"})

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["currency"] == "EUR"


@pytest.mark.asyncio
async def test_update_email_conflict():
    from app.main import app

    user = _make_user()
    db = _db_email_conflict()
    _override_user_and_db(app, user, db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.patch("/user/me", json={"email": "taken@example.com"})

    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "already in use" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_me_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.patch("/user/me", json={"currency": "USD"})

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# A-08: POST /user/me/password
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_password_happy():
    from app.main import app

    user = _make_user()
    db = _db_no_email_conflict()
    _override_user_and_db(app, user, db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/user/me/password",
            json={"old_password": _PASSWORD, "new_password": "newpassword99"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_change_password_wrong_old():
    from app.main import app

    user = _make_user()
    db = _db_no_email_conflict()
    _override_user_and_db(app, user, db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/user/me/password",
            json={"old_password": "wrongpassword", "new_password": "newpassword99"},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 400
    assert "incorrect" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_change_password_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/user/me/password",
            json={"old_password": _PASSWORD, "new_password": "newpassword99"},
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# A-07: DELETE /user/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_account_happy():
    from app.main import app

    user = _make_user()
    db = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    _override_user_and_db(app, user, db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete("/user/me")

    app.dependency_overrides.clear()
    assert resp.status_code == 204
    db.delete.assert_called_once_with(user)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_account_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.delete("/user/me")

    assert resp.status_code == 401
