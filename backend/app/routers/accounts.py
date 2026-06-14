import logging
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountOut, AccountUpdate
from app.schemas.transfer import TransferCreate, TransferOut
from app.services import account_service, transfer_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _to_out(account: Account, balance_cents: int) -> AccountOut:
    return AccountOut(
        id=account.id,
        user_id=account.user_id,
        name=account.name,
        type=account.type,
        initial_balance_cents=account.initial_balance_cents,
        balance_cents=balance_cents,
        is_archived=account.is_archived,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("", response_model=list[AccountOut])
@limiter.limit("300/minute")
async def list_accounts(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pairs = await account_service.get_all(current_user.id, db)
    return [_to_out(account, balance) for account, balance in pairs]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_account(
    body: AccountCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.create(
        user_id=current_user.id,
        name=body.name,
        type_=body.type,
        initial_balance_cents=body.initial_balance_cents,
        db=db,
    )
    balance = await account_service.compute_balance(account, db)
    return _to_out(account, balance)


@router.patch("/{account_id}", response_model=AccountOut)
@limiter.limit("300/minute")
async def update_account(
    account_id: uuid.UUID,
    body: AccountUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await account_service.update(
        account_id=account_id,
        user_id=current_user.id,
        db=db,
        name=body.name,
        type_=body.type,
        initial_balance_cents=body.initial_balance_cents,
        is_archived=body.is_archived,
    )
    balance = await account_service.compute_balance(account, db)
    return _to_out(account, balance)


@router.delete("/{account_id}")
@limiter.limit("300/minute")
async def delete_account(
    account_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await account_service.delete(account_id=account_id, user_id=current_user.id, db=db)
    return {"ok": True}


@router.get("/transfers", response_model=list[TransferOut])
@limiter.limit("300/minute")
async def list_transfers(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transfer_service.list_all(current_user.id, db)


@router.post("/transfers", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_transfer(
    body: TransferCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transfer_service.create(
        user_id=current_user.id,
        from_account_id=body.from_account_id,
        to_account_id=body.to_account_id,
        amount_cents=body.amount_cents,
        tx_date=body.tx_date,
        note=body.note,
        db=db,
    )
