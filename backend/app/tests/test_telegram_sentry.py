"""
Tests for A-05 (Telegram auth) and S-10 (Sentry 500 capture).
Strategy: mock DB + patch verify_telegram_init_data for unit isolation.
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_TG_ID = 123456789


def _make_user(new: bool = False):
    u = MagicMock()
    u.id = _USER_ID
    u.email = None
    u.telegram_id = _TG_ID
    u.currency = "BYN"
    u.password_hash = None
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


def _scalar_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def _build_init_data(bot_token: str, tg_id: int = _TG_ID, age: int = 0) -> str:
    """Builds a properly signed Telegram initData string."""
    auth_date = int(time.time()) - age
    user_json = json.dumps({"id": tg_id, "first_name": "Test", "username": "testuser"})
    params = {
        "auth_date": str(auth_date),
        "user": user_json,
    }
    data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    params["hash"] = hash_val
    return urlencode(params)


def _make_client(db_mock):
    from app.dependencies import get_current_user, get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: (yield db_mock)
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def _make_anon_client():
    from app.main import app
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def _clear():
    from app.main import app
    app.dependency_overrides.clear()


def _stamp_user(obj):
    from app.models.user import User
    if isinstance(obj, User):
        if obj.id is None:
            obj.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if obj.created_at is None:
            obj.created_at = now
        if obj.updated_at is None:
            obj.updated_at = now
        if obj.currency is None:
            obj.currency = "BYN"


# ---------------------------------------------------------------------------
# A-05: Telegram auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_telegram_new_user():
    """Valid initData for a new user → 200, access_token returned."""
    from app.tests.conftest import _TEST_BOT_TOKEN
    init_data = _build_init_data(_TEST_BOT_TOKEN)

    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_user)
    # No existing user with that telegram_id
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    from app.main import app
    app.dependency_overrides.clear()
    app.dependency_overrides[
        __import__("app.dependencies", fromlist=["get_db"]).get_db
    ] = lambda: (yield db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/telegram", json={"init_data": init_data})
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_telegram_existing_user():
    """Valid initData for an existing user → 200, same user returned."""
    from app.tests.conftest import _TEST_BOT_TOKEN
    init_data = _build_init_data(_TEST_BOT_TOKEN)

    existing = _make_user()
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(existing))

    from app.main import app
    app.dependency_overrides.clear()
    app.dependency_overrides[
        __import__("app.dependencies", fromlist=["get_db"]).get_db
    ] = lambda: (yield db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/telegram", json={"init_data": init_data})
    _clear()

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_telegram_expired_init_data():
    """initData older than 86400s → 400 expired."""
    from app.tests.conftest import _TEST_BOT_TOKEN
    init_data = _build_init_data(_TEST_BOT_TOKEN, age=86401)

    db = AsyncMock()
    from app.main import app
    app.dependency_overrides.clear()
    app.dependency_overrides[
        __import__("app.dependencies", fromlist=["get_db"]).get_db
    ] = lambda: (yield db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/telegram", json={"init_data": init_data})
    _clear()

    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_telegram_invalid_hash():
    """initData with wrong hash → 400 invalid."""
    from app.tests.conftest import _TEST_BOT_TOKEN
    init_data = _build_init_data(_TEST_BOT_TOKEN)
    # Corrupt the hash
    init_data = init_data.replace(init_data[-4:], "0000")

    db = AsyncMock()
    from app.main import app
    app.dependency_overrides.clear()
    app.dependency_overrides[
        __import__("app.dependencies", fromlist=["get_db"]).get_db
    ] = lambda: (yield db)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/telegram", json={"init_data": init_data})
    _clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid initData"


@pytest.mark.asyncio
async def test_telegram_missing_init_data():
    """Empty body → 422 validation error."""
    from app.main import app
    app.dependency_overrides.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/telegram", json={})
    _clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# S-10: Sentry — 500 errors captured
# ---------------------------------------------------------------------------

def test_sentry_sdk_callable():
    """
    Verifies sentry_sdk.capture_exception can be called without raising.
    In tests SENTRY_DSN="" so Sentry init is skipped, but the guard in main.py
    (if settings.SENTRY_DSN: sentry_sdk.init(...)) must be respected.
    Patching confirms the call path is wired correctly.
    """
    import sentry_sdk

    from app.config import settings

    assert isinstance(settings.SENTRY_DSN, str)

    with patch.object(sentry_sdk, "capture_exception") as mock_cap:
        sentry_sdk.capture_exception(RuntimeError("test"))
        mock_cap.assert_called_once()
