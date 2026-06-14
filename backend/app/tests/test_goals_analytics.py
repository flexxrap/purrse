"""
Tests for D-05 (Goals CRUD) and D-01/D-02/D-03 (Analytics).
Strategy: override get_current_user + get_db — no real DB needed.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_GOAL_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    return u


def _make_goal(**kwargs):
    g = MagicMock()
    g.id = kwargs.get("id", _GOAL_ID)
    g.user_id = _USER_ID
    g.name = kwargs.get("name", "New Car")
    g.target_cents = kwargs.get("target_cents", 500000)
    g.current_cents = kwargs.get("current_cents", 100000)
    g.deadline = kwargs.get("deadline", None)
    now = datetime.now(timezone.utc)
    g.created_at = now
    g.updated_at = now
    return g


def _scalar_one_or_none(value):
    r = MagicMock()
    r.scalar_one_or_none = MagicMock(return_value=value)
    return r


def _scalars_list(items):
    sc = MagicMock()
    sc.all = MagicMock(return_value=items)
    r = MagicMock()
    r.scalars = MagicMock(return_value=sc)
    return r


def _rows_list(rows):
    r = MagicMock()
    r.all = MagicMock(return_value=rows)
    return r


def _stamp_goal(obj):
    from app.models.goal import Goal
    if isinstance(obj, Goal):
        if obj.id is None:
            obj.id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        if obj.created_at is None:
            obj.created_at = now
        if obj.updated_at is None:
            obj.updated_at = now


def _make_client(db_mock):
    from app.dependencies import get_current_user, get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: (yield db_mock)
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def _clear():
    from app.main import app
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# D-05: Goals CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_goals():
    goal = _make_goal()
    db = AsyncMock()
    # get_all calls: 1) select goals, 2) select for avg balance
    db.execute = AsyncMock(side_effect=[
        _scalars_list([goal]),
        _rows_list([]),          # no transaction data → monthly_free = 0
    ])

    async with _make_client(db) as c:
        response = await c.get("/goals")
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert body[0]["name"] == "New Car"
    assert body[0]["target_cents"] == 500000
    assert body[0]["months_to_completion"] is None  # no free balance data


@pytest.mark.asyncio
async def test_create_goal():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_goal)
    # After refresh: avg balance query
    db.execute = AsyncMock(return_value=_rows_list([]))

    async with _make_client(db) as c:
        response = await c.post("/goals", json={
            "name": "Vacation",
            "target_cents": 200000,
            "current_cents": 0,
        })
    _clear()

    assert response.status_code == 201
    assert response.json()["name"] == "Vacation"


@pytest.mark.asyncio
async def test_create_goal_with_months_to_completion():
    """When free monthly balance > 0, months_to_completion is computed."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_goal)

    # Simulate avg balance: income 30000, expense 0 → free = 10000/month
    income_row = MagicMock()
    income_row.type = "income"
    income_row.total = 30000
    db.execute = AsyncMock(return_value=_rows_list([income_row]))

    async with _make_client(db) as c:
        response = await c.post("/goals", json={
            "name": "Laptop",
            "target_cents": 50000,
            "current_cents": 0,
        })
    _clear()

    assert response.status_code == 201
    body = response.json()
    # remaining=50000, monthly_free=10000 → 5 months
    assert body["months_to_completion"] == 5


@pytest.mark.asyncio
async def test_update_goal_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    async with _make_client(db) as c:
        response = await c.patch(f"/goals/{_GOAL_ID}", json={"name": "Updated"})
    _clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_goal_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    async with _make_client(db) as c:
        response = await c.delete(f"/goals/{_GOAL_ID}")
    _clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_goals_unauthenticated():
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.get("/goals")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# D-01: Analytics summary
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analytics_summary():
    income_row = MagicMock()
    income_row.type = "income"
    income_row.total = 500000

    expense_row = MagicMock()
    expense_row.type = "expense"
    expense_row.total = 200000

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_rows_list([income_row, expense_row]))

    async with _make_client(db) as c:
        response = await c.get("/analytics/summary", params={"month": "2026-06"})
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-06"
    assert body["income_cents"] == 500000
    assert body["expense_cents"] == 200000
    assert body["balance_cents"] == 300000


@pytest.mark.asyncio
async def test_analytics_summary_empty():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_rows_list([]))

    async with _make_client(db) as c:
        response = await c.get("/analytics/summary")
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert body["income_cents"] == 0
    assert body["expense_cents"] == 0
    assert body["balance_cents"] == 0


@pytest.mark.asyncio
async def test_analytics_summary_bad_month():
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.get("/analytics/summary", params={"month": "not-a-date"})
    _clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# D-02: Category breakdown
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analytics_categories_top5_plus_other():
    # 6 categories → top 5 + Other
    rows = []
    for i in range(6):
        r = MagicMock()
        r.category_id = uuid.uuid4()
        r.name = f"Cat{i}"
        r.color = "#AABBCC"
        r.type = "expense"
        r.total_cents = (6 - i) * 1000  # descending: 6000,5000,4000,3000,2000,1000
        rows.append(r)

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_rows_list(rows))

    async with _make_client(db) as c:
        response = await c.get("/analytics/categories", params={"month": "2026-06"})
    _clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 6  # 5 + Other
    assert items[-1]["name"] == "Other"
    assert items[-1]["total_cents"] == 1000


@pytest.mark.asyncio
async def test_analytics_categories_empty():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_rows_list([]))

    async with _make_client(db) as c:
        response = await c.get("/analytics/categories", params={"month": "2026-06"})
    _clear()

    assert response.status_code == 200
    assert response.json()["items"] == []


# ---------------------------------------------------------------------------
# D-03: Trend
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analytics_trend():
    row = MagicMock()
    row.year = 2026
    row.month = 5
    row.type = "income"
    row.total = 100000

    db = AsyncMock()
    db.execute = AsyncMock(return_value=_rows_list([row]))

    async with _make_client(db) as c:
        response = await c.get("/analytics/trend", params={"months": 3})
    _clear()

    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 3
    # oldest first — check May 2026 has the income
    may = next((i for i in items if i["month"] == "2026-05"), None)
    assert may is not None
    assert may["income_cents"] == 100000
    assert may["expense_cents"] == 0


@pytest.mark.asyncio
async def test_analytics_trend_unauth():
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.get("/analytics/trend")
    assert response.status_code == 401
