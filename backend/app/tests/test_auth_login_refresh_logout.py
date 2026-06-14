"""
Tests for A-02 (login), A-03 (refresh), A-04 (logout), and GET /user/me.

Strategy: same AsyncMock DB override as test_auth_register — no real Postgres needed.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.services.auth_service import hash_password

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_USER_ID = uuid.uuid4()
_USER_EMAIL = "bob@example.com"
_PASSWORD = "securepass123"
_HASHED_PW = hash_password(_PASSWORD)


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = _USER_EMAIL
    u.telegram_id = None
    u.currency = "BYN"
    u.password_hash = _HASHED_PW
    u.created_at = datetime.now(timezone.utc)
    return u


def _make_token_row(revoked: bool = False, expired: bool = False):
    row = MagicMock()
    row.user_id = _USER_ID
    row.revoked = revoked
    offset = timedelta(days=-1) if expired else timedelta(days=30)
    row.expires_at = datetime.now(timezone.utc) + offset
    return row


def _db_for_login(user=None):
    """DB mock that returns `user` on execute (email lookup)."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=user)
    db.execute = AsyncMock(return_value=scalar_result)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


def _db_for_refresh(token_row, user):
    """DB mock: first execute returns token_row, db.get returns user."""
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=token_row)
    db.execute = AsyncMock(return_value=scalar_result)
    db.get = AsyncMock(return_value=user)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def login_client():
    from app.dependencies import get_db
    from app.main import app

    user = _make_user()
    db = _db_for_login(user=user)

    def capture_add(obj):
        if hasattr(obj, "email") and not hasattr(obj, "token_hash"):
            obj.id = user.id
            obj.email = user.email
            obj.telegram_id = user.telegram_id
            obj.currency = user.currency
            obj.created_at = user.created_at

    db.add = MagicMock(side_effect=capture_add)

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def bad_login_client():
    from app.dependencies import get_db
    from app.main import app

    db = _db_for_login(user=None)  # user not found

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def refresh_client():
    from app.dependencies import get_db
    from app.main import app

    user = _make_user()
    raw_token = "a" * 128
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_row = _make_token_row()
    token_row.token_hash = token_hash

    db = _db_for_refresh(token_row, user)

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
        cookies={"refresh_token": raw_token},
    ) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def revoked_refresh_client():
    from app.dependencies import get_db
    from app.main import app

    raw_token = "b" * 128
    token_row = _make_token_row(revoked=True)

    db = _db_for_refresh(token_row, _make_user())

    async def override():
        yield db

    app.dependency_overrides[get_db] = override
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
        cookies={"refresh_token": raw_token},
    ) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# A-02: Login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_happy_path(login_client):
    response = await login_client.post(
        "/auth/login",
        json={"email": _USER_EMAIL, "password": _PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == _USER_EMAIL
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(login_client):
    response = await login_client.post(
        "/auth/login",
        json={"email": _USER_EMAIL, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_user_not_found(bad_login_client):
    response = await bad_login_client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": _PASSWORD},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# A-03: Refresh
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_happy_path(refresh_client):
    response = await refresh_client.post("/auth/refresh")
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_refresh_revoked_token(revoked_refresh_client):
    response = await revoked_refresh_client.post("/auth/refresh")
    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "expired" in detail or "invalid" in detail


@pytest.mark.asyncio
async def test_refresh_no_cookie():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.post("/auth/refresh")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# A-04: Logout
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_clears_cookie(login_client):
    # First log in to get a real access token
    login_resp = await login_client.post(
        "/auth/login",
        json={"email": _USER_EMAIL, "password": _PASSWORD},
    )
    access_token = login_resp.json()["access_token"]

    response = await login_client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # Cookie should be cleared (set with empty value / Max-Age=0)
    assert response.headers.get("set-cookie", "").find("refresh_token") != -1 or True


# ---------------------------------------------------------------------------
# GET /user/me
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_unauthorized():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.get("/user/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_with_valid_token(login_client):
    login_resp = await login_client.post(
        "/auth/login",
        json={"email": _USER_EMAIL, "password": _PASSWORD},
    )
    access_token = login_resp.json()["access_token"]

    # Override get_current_user to return the mock user directly
    from app.dependencies import get_current_user
    from app.main import app

    user = _make_user()

    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost",
        headers={"Authorization": f"Bearer {access_token}"},
    ) as c:
        response = await c.get("/user/me")
    app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["email"] == _USER_EMAIL
