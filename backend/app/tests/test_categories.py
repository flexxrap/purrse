"""
Tests for T-05: GET/POST/PATCH/DELETE /categories.

Strategy: override get_current_user + get_db per test — no real DB needed.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    return u


def _make_category(**kwargs):
    c = MagicMock()
    c.id = kwargs.get("id", _CAT_ID)
    c.user_id = _USER_ID
    c.name = kwargs.get("name", "Food")
    c.color = kwargs.get("color", "#FF5733")
    c.type = kwargs.get("type", "expense")
    c.created_at = datetime.now(timezone.utc)
    return c


def _scalars_result(items: list):
    scalars = MagicMock()
    scalars.all = MagicMock(return_value=items)
    result = MagicMock()
    result.scalars = MagicMock(return_value=scalars)
    return result


def _scalar_one_result(value):
    result = MagicMock()
    result.scalar_one = MagicMock(return_value=value)
    return result


def _scalar_one_or_none_result(value):
    result = MagicMock()
    result.scalar_one_or_none = MagicMock(return_value=value)
    return result


def _stamp_obj(obj):
    """Simulate what db.refresh does: populate server-side defaults."""
    from app.models.category import Category
    if isinstance(obj, Category):
        if obj.id is None:
            obj.id = uuid.uuid4()
        if obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)


def _make_db(execute_return=None, count: int = 0, found=None):
    """Build a DB mock configured for a specific scenario."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.delete = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_obj)
    if execute_return is not None:
        db.execute = AsyncMock(return_value=execute_return)
    return db


def _make_client(db_mock):
    from app.dependencies import get_current_user, get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: (yield db_mock)
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_categories():
    cat = _make_category()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_result([cat]))

    async with _make_client(db) as c:
        response = await c.get("/categories")

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body[0]["name"] == "Food"
    assert body[0]["color"] == "#FF5733"
    assert body[0]["type"] == "expense"


@pytest.mark.asyncio
async def test_create_category():
    db = _make_db(execute_return=_scalar_one_result(0))

    async with _make_client(db) as c:
        response = await c.post(
            "/categories",
            json={"name": "Salary", "color": "#00FF00", "type": "income"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_duplicate_name_allowed():
    """No uniqueness constraint — same name twice is fine."""
    db = _make_db(execute_return=_scalar_one_result(1))

    async with _make_client(db) as c:
        response = await c.post(
            "/categories",
            json={"name": "Food", "color": "#FF5733", "type": "expense"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_category_limit_reached():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_result(50))

    async with _make_client(db) as c:
        response = await c.post(
            "/categories",
            json={"name": "Extra", "color": "#AABBCC", "type": "expense"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Maximum 50 categories reached"


@pytest.mark.asyncio
async def test_create_category_bad_color():
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.post(
            "/categories",
            json={"name": "Bad", "color": "red", "type": "expense"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_category_bad_type():
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.post(
            "/categories",
            json={"name": "Bad", "color": "#AABBCC", "type": "other"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_category_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

    async with _make_client(db) as c:
        response = await c.patch(
            f"/categories/{_CAT_ID}",
            json={"name": "Updated"},
        )

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

    async with _make_client(db) as c:
        response = await c.delete(f"/categories/{_CAT_ID}")

    from app.main import app
    app.dependency_overrides.clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_categories_unauthenticated():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.get("/categories")

    assert response.status_code == 401
