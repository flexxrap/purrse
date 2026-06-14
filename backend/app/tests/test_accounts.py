"""
Tests for T-11: multi-account support (accounts CRUD, balances, transfers).
Strategy: override get_current_user + get_db — no real DB needed.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

_USER_ID = uuid.uuid4()
_ACCOUNT_ID = uuid.uuid4()
_ACCOUNT_ID_2 = uuid.uuid4()
_TODAY = date.today()


def _make_user():
    u = MagicMock()
    u.id = _USER_ID
    return u


def _make_account(**kwargs):
    a = MagicMock()
    a.id = kwargs.get("id", _ACCOUNT_ID)
    a.user_id = _USER_ID
    a.name = kwargs.get("name", "Cash")
    a.type = kwargs.get("type", "cash")
    a.initial_balance_cents = kwargs.get("initial_balance_cents", 10000)
    a.is_archived = kwargs.get("is_archived", False)
    a.created_at = datetime.now(timezone.utc)
    a.updated_at = datetime.now(timezone.utc)
    return a


def _make_transfer(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", uuid.uuid4())
    t.user_id = _USER_ID
    t.from_account_id = kwargs.get("from_account_id", _ACCOUNT_ID)
    t.to_account_id = kwargs.get("to_account_id", _ACCOUNT_ID_2)
    t.amount_cents = kwargs.get("amount_cents", 5000)
    t.note = kwargs.get("note", None)
    t.tx_date = kwargs.get("tx_date", _TODAY)
    t.created_at = datetime.now(timezone.utc)
    return t


def _scalars_result(items):
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
    from app.models.account import Account
    from app.models.transfer import Transfer

    now = datetime.now(timezone.utc)
    if isinstance(obj, Account):
        if obj.id is None:
            obj.id = uuid.uuid4()
        if obj.is_archived is None:
            obj.is_archived = False
        if obj.created_at is None:
            obj.created_at = now
        if obj.updated_at is None:
            obj.updated_at = now
    elif isinstance(obj, Transfer):
        if obj.id is None:
            obj.id = uuid.uuid4()
        if obj.created_at is None:
            obj.created_at = now


def _make_client(db_mock):
    from app.dependencies import get_current_user, get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: (yield db_mock)
    app.dependency_overrides[get_current_user] = lambda: _make_user()
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


def _clear():
    from app.main import app
    app.dependency_overrides.clear()


# Three db.execute calls made by account_service.compute_balance per account
def _balance_calls(tx_delta=0, transfers_in=0, transfers_out=0):
    return [
        _scalar_one_result(tx_delta),
        _scalar_one_result(transfers_in),
        _scalar_one_result(transfers_out),
    ]


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_accounts_happy():
    account = _make_account()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalars_result([account]),
        *_balance_calls(tx_delta=5000),
    ])

    async with _make_client(db) as c:
        response = await c.get("/accounts")
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Cash"
    assert body[0]["balance_cents"] == 15000  # 10000 initial + 5000 tx delta


@pytest.mark.asyncio
async def test_list_accounts_unauthorized():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        response = await c.get("/accounts")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_account_happy():
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_result(0),  # count check
        *_balance_calls(),
    ])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_obj)

    async with _make_client(db) as c:
        response = await c.post("/accounts", json={
            "name": "Cash",
            "type": "cash",
            "initial_balance_cents": 10000,
        })
    _clear()

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cash"
    assert body["type"] == "cash"
    assert body["balance_cents"] == 10000


@pytest.mark.asyncio
async def test_create_account_limit_reached():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_result(20))

    async with _make_client(db) as c:
        response = await c.post("/accounts", json={
            "name": "Extra",
            "type": "cash",
            "initial_balance_cents": 0,
        })
    _clear()

    assert response.status_code == 400
    assert "Maximum" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_account_bad_type():
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.post("/accounts", json={
            "name": "Bad",
            "type": "crypto",
            "initial_balance_cents": 0,
        })
    _clear()

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_account_happy():
    account = _make_account()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none_result(account),
        *_balance_calls(),
    ])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_obj)

    async with _make_client(db) as c:
        response = await c.patch(f"/accounts/{_ACCOUNT_ID}", json={"name": "Renamed"})
    _clear()

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


@pytest.mark.asyncio
async def test_update_account_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

    async with _make_client(db) as c:
        response = await c.patch(f"/accounts/{_ACCOUNT_ID}", json={"name": "X"})
    _clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_account_happy():
    account = _make_account()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none_result(account),  # get_one
        _scalar_one_result(0),  # transaction count
        _scalar_one_result(0),  # recurring count
        _scalar_one_result(0),  # transfer count
    ])
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    async with _make_client(db) as c:
        response = await c.delete(f"/accounts/{_ACCOUNT_ID}")
    _clear()

    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_delete_account_with_transactions():
    account = _make_account()
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none_result(account),  # get_one
        _scalar_one_result(3),  # transaction count > 0
    ])

    async with _make_client(db) as c:
        response = await c.delete(f"/accounts/{_ACCOUNT_ID}")
    _clear()

    assert response.status_code == 400
    assert "transactions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_account_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

    async with _make_client(db) as c:
        response = await c.delete(f"/accounts/{_ACCOUNT_ID}")
    _clear()

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_transfer_happy():
    from_account = _make_account(id=_ACCOUNT_ID)
    to_account = _make_account(id=_ACCOUNT_ID_2)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        _scalar_one_or_none_result(from_account),  # get_one(from)
        _scalar_one_or_none_result(to_account),    # get_one(to)
    ])
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_stamp_obj)

    async with _make_client(db) as c:
        response = await c.post("/accounts/transfers", json={
            "from_account_id": str(_ACCOUNT_ID),
            "to_account_id": str(_ACCOUNT_ID_2),
            "amount_cents": 5000,
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 201
    body = response.json()
    assert body["amount_cents"] == 5000
    assert body["from_account_id"] == str(_ACCOUNT_ID)
    assert body["to_account_id"] == str(_ACCOUNT_ID_2)


@pytest.mark.asyncio
async def test_create_transfer_same_account():
    db = AsyncMock()

    async with _make_client(db) as c:
        response = await c.post("/accounts/transfers", json={
            "from_account_id": str(_ACCOUNT_ID),
            "to_account_id": str(_ACCOUNT_ID),
            "amount_cents": 5000,
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_transfer_account_not_found():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

    async with _make_client(db) as c:
        response = await c.post("/accounts/transfers", json={
            "from_account_id": str(_ACCOUNT_ID),
            "to_account_id": str(_ACCOUNT_ID_2),
            "amount_cents": 5000,
            "tx_date": str(_TODAY),
        })
    _clear()

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_transfers_happy():
    transfer = _make_transfer()
    db = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_result([transfer]))

    async with _make_client(db) as c:
        response = await c.get("/accounts/transfers")
    _clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["amount_cents"] == 5000


@pytest.mark.asyncio
async def test_list_transfers_unauthorized():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as c:
        response = await c.get("/accounts/transfers")
    assert response.status_code == 401
