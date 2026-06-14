"""
Integration tests for the full auth flow against a real PostgreSQL database.

These tests exercise JWT signing, bcrypt hashing, refresh token rotation,
and audit log writes — things that mocked unit tests cannot catch.

Requires DATABASE_URL to point to a live Postgres instance (set in CI via
the postgres service, and locally via .env).
"""
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# Import every model so SQLAlchemy registers them with Base.metadata before
# create_all is called. Order does not matter — SA resolves FK dependencies.
import app.models.audit_log  # noqa: F401
import app.models.budget  # noqa: F401
import app.models.category  # noqa: F401
import app.models.goal  # noqa: F401
import app.models.refresh_token  # noqa: F401
import app.models.transaction  # noqa: F401
import app.models.user  # noqa: F401
from app.config import settings
from app.database import Base
from app.dependencies import get_db
from app.main import app


def _email() -> str:
    # Use example.com — explicitly reserved for testing per RFC 2606
    return f"integ_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
async def client():
    """AsyncClient wired to the real test DB (tables created on first call)."""
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


class TestRegisterIntegration:
    async def test_register_creates_user_and_returns_tokens(self, client):
        resp = await client.post(
            "/auth/register",
            json={"email": _email(), "password": "securepass123"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "refresh_token" in resp.cookies

    async def test_register_duplicate_email_rejected(self, client):
        email = _email()
        await client.post("/auth/register", json={"email": email, "password": "securepass123"})
        resp = await client.post(
            "/auth/register", json={"email": email, "password": "securepass123"}
        )
        assert resp.status_code == 400

    async def test_register_unauthorized_without_token(self, client):
        resp = await client.get("/user/me")
        assert resp.status_code == 401


class TestLoginIntegration:
    async def test_login_returns_valid_access_token(self, client):
        email, pw = _email(), "securepass123"
        await client.post("/auth/register", json={"email": email, "password": pw})

        # Login uses JSON body with "email" field (not OAuth2 form)
        resp = await client.post("/auth/login", json={"email": email, "password": pw})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_wrong_password_returns_401(self, client):
        email = _email()
        await client.post("/auth/register", json={"email": email, "password": "securepass123"})

        resp = await client.post(
            "/auth/login", json={"email": email, "password": "wrongpassword"}
        )
        assert resp.status_code == 401

    async def test_unknown_email_returns_401(self, client):
        resp = await client.post(
            "/auth/login", json={"email": "nobody@example.com", "password": "anypassword"}
        )
        assert resp.status_code == 401


class TestRefreshIntegration:
    async def test_refresh_issues_new_access_token(self, client):
        email, pw = _email(), "securepass123"
        reg = await client.post("/auth/register", json={"email": email, "password": pw})
        old_token = reg.json()["access_token"]

        resp = await client.post("/auth/refresh")
        assert resp.status_code == 200
        assert resp.json()["access_token"] != old_token

    async def test_refresh_without_cookie_returns_401(self, client):
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 401

    async def test_refresh_token_is_rotated(self, client):
        """Using the same refresh token twice should fail (rotation)."""
        email, pw = _email(), "securepass123"
        reg = await client.post("/auth/register", json={"email": email, "password": pw})
        old_cookie = reg.cookies.get("refresh_token")

        # Use it once — should succeed and set a new cookie
        await client.post("/auth/refresh")

        # Put the OLD cookie back and try again — should be rejected
        client.cookies.set("refresh_token", old_cookie)
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 401


class TestLogoutIntegration:
    async def test_logout_clears_session(self, client):
        email, pw = _email(), "securepass123"
        reg = await client.post("/auth/register", json={"email": email, "password": pw})
        token = reg.json()["access_token"]

        logout_resp = await client.post(
            "/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )
        assert logout_resp.status_code == 200

        # refresh should now fail since the token was revoked
        resp = await client.post("/auth/refresh")
        assert resp.status_code == 401

    async def test_logout_without_auth_returns_401(self, client):
        resp = await client.post("/auth/logout")
        assert resp.status_code == 401
