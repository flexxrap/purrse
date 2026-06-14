"""
Tests for POST /auth/register.

Strategy: override get_db with an AsyncMock so tests run without a real
Postgres instance. The service logic (hashing, JWT, audit) is exercised
through the real code path; only the DB I/O is stubbed.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(email: str = "alice@example.com") -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.telegram_id = None
    user.currency = "BYN"
    user.created_at = datetime.now(timezone.utc)
    return user


def _make_db_mock(existing_user=None):
    """Return an AsyncMock that behaves like AsyncSession."""
    db = AsyncMock()

    # scalar_one_or_none() returns existing_user (None = email free)
    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none = MagicMock(return_value=existing_user)
    db.execute = AsyncMock(return_value=scalar_result)

    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()

    # After commit, refresh populates the user object — simulate by doing nothing
    # (the mock user already has all fields set)
    db.refresh = AsyncMock()

    return db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_user():
    return _make_user()


@pytest.fixture
async def client(fresh_user):
    from app.dependencies import get_db
    from app.main import app

    db_mock = _make_db_mock(existing_user=None)

    # After flush, the router calls db.refresh(user) — we want user.id to exist.
    # Inject the user into db.add so refresh can find it.
    added_objects = []

    def capture_add(obj):
        added_objects.append(obj)
        # Stamp the User with an id so create_access_token has something to encode
        if hasattr(obj, "email") and not hasattr(obj, "token_hash"):
            obj.id = fresh_user.id
            obj.email = fresh_user.email
            obj.telegram_id = fresh_user.telegram_id
            obj.currency = fresh_user.currency
            obj.created_at = fresh_user.created_at

    db_mock.add = MagicMock(side_effect=capture_add)

    async def override_get_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def client_duplicate():
    """Client whose DB mock simulates an already-registered email."""
    from app.dependencies import get_db
    from app.main import app

    existing = _make_user()
    db_mock = _make_db_mock(existing_user=existing)

    async def override_get_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_happy_path(client):
    response = await client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "securepass123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
    assert body["user"]["email"] == "alice@example.com"
    assert body["user"]["currency"] == "BYN"
    # Refresh cookie must be set
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client_duplicate):
    response = await client_duplicate.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "securepass123"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_password_too_short(client):
    response = await client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    response = await client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "securepass123"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields(client):
    response = await client.post("/auth/register", json={})
    assert response.status_code == 422
