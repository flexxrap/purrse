"""
Tests for T-01/T-02/T-03/T-04: Transactions CRUD.
Strategy: override get_current_user + get_db — no real DB needed.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_TX_ID = uuid.uuid4()
_CAT_ID = uuid.uuid4()
_ACCOUNT_ID = uuid.uuid4()
_TODAY = date.today()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    return u


def _make_tx(**kwargs):
    tx = MagicMock()
    tx.id = kwargs.get("id", _TX_ID)
    tx.user_id = _USER_ID
    tx.account_id = kwargs.get("account_id", _ACCOUNT_ID)
    tx.category_id = kwargs.get("category_id", _CAT_ID)
    tx.amount_cents = kwargs.get("amount_cents", 1000)
    tx.note = kwargs.get("note", None)
    tx.tx_date = kwargs.get("tx_date", _TODAY)
    tx.created_at = datetime.now(timezone.utc)
    tx.updated_at = datetime.now(timezone.utc)
    tx.deleted_at = None
    return tx


def _make_cat():
    c = MagicMock()
    c.id = _CAT_ID
    c.user_id = _USER_ID
    c.type = "expense"
    return c


def _make_account():
    a = MagicMock()
    a.id = _ACCOUNT_ID
    a.user_id = _USER_ID
    return a


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


def _stamp(obj):
    from app.models.transaction import Transaction
    if isinstance(obj, Transaction):
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
# T-01: Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_transaction():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none(_make_cat()),      # transaction_service: category ownership check
        _scalar_one_or_none(_make_account()),  # transaction_service: account ownership check
        _scalar_one_or_none(None),             # check_and_alert: no budget → early return
    ])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp)

    async with _make_client(db) as c:
        response = await c.post("/transactions", json={
            "account_id": str(_ACCOUNT_ID),
            "amount_cents": 1500,
            "category_id": str(_CAT_ID),
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 201
    assert response.json()["amount_cents"] == 1500


@pytest.mark.asyncio
async def test_create_transaction_bad_category():
    """Category not found → 400."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    async with _make_client(db) as c:
        response = await c.post("/transactions", json={
            "account_id": str(_ACCOUNT_ID),
            "amount_cents": 500,
            "category_id": str(uuid.uuid4()),
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 400
    assert "Category" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transaction_bad_account():
    """Account not found or not owned by user → 400."""
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none(_make_cat()),  # category ownership check passes
        _scalar_one_or_none(None),         # account ownership check fails
    ])

    async with _make_client(db) as c:
        response = await c.post("/transactions", json={
            "account_id": str(uuid.uuid4()),
            "amount_cents": 500,
            "category_id": str(_CAT_ID),
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 400
    assert "Account" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transaction_zero_amount():
    """amount_cents must be > 0 → 422."""
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.post("/transactions", json={
            "account_id": str(_ACCOUNT_ID),
            "amount_cents": 0,
            "category_id": str(_CAT_ID),
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# T-02: List with cursor pagination
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_transactions_default():
    tx = _make_tx()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_list([tx]))

    async with _make_client(db) as c:
        response = await c.get("/transactions")
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "next_cursor" in body
    assert len(body["items"]) == 1
    assert body["next_cursor"] is None


@pytest.mark.asyncio
async def test_list_transactions_with_filters():
    tx = _make_tx()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_list([tx]))

    async with _make_client(db) as c:
        response = await c.get(
            "/transactions",
            params={
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "category_id": str(_CAT_ID),
                "limit": 10,
            },
        )
    _clear()

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_transactions_with_account_filter():
    tx = _make_tx()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_list([tx]))

    async with _make_client(db) as c:
        response = await c.get("/transactions", params={"account_id": str(_ACCOUNT_ID)})
    _clear()

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_cursor_pagination():
    """When service returns limit+1 rows, next_cursor is set."""
    ids = [uuid.uuid4() for _ in range(3)]
    # limit=2, return 3 rows → cursor should be ids[1] (last kept item)
    txs = [_make_tx(id=i) for i in ids]
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_list(txs))

    async with _make_client(db) as c:
        response = await c.get("/transactions", params={"limit": 2})
    _clear()

    body = response.json()
    assert response.status_code == 200
    assert len(body["items"]) == 2
    assert body["next_cursor"] == str(ids[1])


@pytest.mark.asyncio
async def test_list_transactions_unauth():
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as c:
        response = await c.get("/transactions")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# T-03: Edit
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_transaction():
    tx = _make_tx()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none(tx),   # transaction_service: tx lookup
        _scalar_one_or_none(None), # check_and_alert: no budget → early return
    ])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp)

    async with _make_client(db) as c:
        response = await c.patch(
            f"/transactions/{_TX_ID}",
            json={"amount_cents": 9999},
        )
    _clear()

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_transaction_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    async with _make_client(db) as c:
        response = await c.patch(
            f"/transactions/{_TX_ID}",
            json={"amount_cents": 100},
        )
    _clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# T-04: Soft delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_soft_delete_transaction():
    tx = _make_tx()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(tx))
    db.add = MagicMock()
    db.commit = AsyncMock()

    async with _make_client(db) as c:
        response = await c.delete(f"/transactions/{_TX_ID}")
    _clear()

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    # deleted_at must have been set on the tx object
    assert tx.deleted_at is not None


@pytest.mark.asyncio
async def test_soft_delete_wrong_user():
    """Transaction belonging to another user → 404."""
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none(None))

    async with _make_client(db) as c:
        response = await c.delete(f"/transactions/{uuid.uuid4()}")
    _clear()

    assert response.status_code == 404
