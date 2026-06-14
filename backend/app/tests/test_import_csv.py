"""Tests for T-08: CSV import"""
import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()
_ACCOUNT_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    u.email = "t08@example.com"
    u.telegram_id = None
    u.currency = "USD"
    u.created_at = datetime.now(timezone.utc)
    return u


def _override(app, user, db):
    from app.dependencies import get_current_user, get_db

    async def override_user():
        return user

    async def override_db():
        yield db

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db


CSV_CONTENT = (
    b"Date,Amount,Category,Note\n"
    b"2026-01-01,50.00,Groceries,lunch\n"
    b"2026-01-02,bad,Groceries,\n"
)


@pytest.mark.asyncio
async def test_import_preview_happy():
    from app.main import app

    _override(app, _make_user(), AsyncMock())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/transactions/import/preview",
            files={"file": ("data.csv", BytesIO(CSV_CONTENT), "text/csv")},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["headers"] == ["Date", "Amount", "Category", "Note"]
    assert data["total_rows"] == 2


@pytest.mark.asyncio
async def test_import_preview_unauthorized():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/transactions/import/preview",
            files={"file": ("data.csv", BytesIO(CSV_CONTENT), "text/csv")},
        )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_import_confirm_happy():
    from app.main import app

    cat = MagicMock()
    cat.id = _CAT_ID
    cat.name = "Groceries"
    cat.user_id = _USER_ID

    db = AsyncMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [cat]
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=execute_result)
    db.commit = AsyncMock()
    db.add_all = MagicMock()

    _override(app, _make_user(), db)

    mapping = json.dumps({"date_col": 0, "amount_col": 1, "category_col": 2, "note_col": 3})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/transactions/import/confirm",
            files={"file": ("data.csv", BytesIO(CSV_CONTENT), "text/csv")},
            data={"mapping": mapping, "account_id": str(_ACCOUNT_ID)},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data
    assert "skipped" in data


@pytest.mark.asyncio
async def test_import_confirm_unauthorized():
    from app.main import app

    mapping = json.dumps({"date_col": 0, "amount_col": 1})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        resp = await c.post(
            "/transactions/import/confirm",
            files={"file": ("data.csv", BytesIO(CSV_CONTENT), "text/csv")},
            data={"mapping": mapping},
        )

    assert resp.status_code == 401
