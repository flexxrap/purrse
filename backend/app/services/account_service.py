import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.recurring import RecurringTransaction
from app.models.transaction import Transaction
from app.models.transfer import Transfer

logger = logging.getLogger(__name__)

MAX_ACCOUNTS_PER_USER = 20


async def compute_balance(account: Account, db: AsyncSession) -> int:
    """Initial balance + (income - expense) on this account + transfers in - transfers out."""
    tx_result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Category.type == "income", Transaction.amount_cents),
                        else_=-Transaction.amount_cents,
                    )
                ),
                0,
            )
        )
        .select_from(Transaction)
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.account_id == account.id, Transaction.deleted_at.is_(None))
    )
    tx_delta = tx_result.scalar_one() or 0

    in_result = await db.execute(
        select(func.coalesce(func.sum(Transfer.amount_cents), 0)).where(
            Transfer.to_account_id == account.id
        )
    )
    out_result = await db.execute(
        select(func.coalesce(func.sum(Transfer.amount_cents), 0)).where(
            Transfer.from_account_id == account.id
        )
    )

    return (
        account.initial_balance_cents
        + tx_delta
        + (in_result.scalar_one() or 0)
        - (out_result.scalar_one() or 0)
    )


async def get_all(user_id: uuid.UUID, db: AsyncSession) -> list[tuple[Account, int]]:
    result = await db.execute(
        select(Account).where(Account.user_id == user_id).order_by(Account.created_at)
    )
    accounts = list(result.scalars().all())
    return [(account, await compute_balance(account, db)) for account in accounts]


async def get_one(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Account:
    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.user_id == user_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account


async def create(
    user_id: uuid.UUID,
    name: str,
    type_: str,
    initial_balance_cents: int,
    db: AsyncSession,
) -> Account:
    count_result = await db.execute(
        select(func.count()).select_from(Account).where(Account.user_id == user_id)
    )
    if count_result.scalar_one() >= MAX_ACCOUNTS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_ACCOUNTS_PER_USER} accounts reached",
        )

    account = Account(
        user_id=user_id,
        name=name,
        type=type_,
        initial_balance_cents=initial_balance_cents,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def update(
    account_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    name: str | None = None,
    type_: str | None = None,
    initial_balance_cents: int | None = None,
    is_archived: bool | None = None,
) -> Account:
    account = await get_one(account_id, user_id, db)

    if name is not None:
        account.name = name
    if type_ is not None:
        account.type = type_
    if initial_balance_cents is not None:
        account.initial_balance_cents = initial_balance_cents
    if is_archived is not None:
        account.is_archived = is_archived

    account.updated_at = datetime.utcnow()
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def delete(account_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    account = await get_one(account_id, user_id, db)

    tx_count = await db.execute(
        select(func.count()).select_from(Transaction).where(Transaction.account_id == account_id)
    )
    if tx_count.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an account with transactions. Archive it instead.",
        )

    rec_count = await db.execute(
        select(func.count())
        .select_from(RecurringTransaction)
        .where(RecurringTransaction.account_id == account_id)
    )
    if rec_count.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an account used by recurring transactions. Archive it instead.",
        )

    transfer_count = await db.execute(
        select(func.count())
        .select_from(Transfer)
        .where(
            (Transfer.from_account_id == account_id) | (Transfer.to_account_id == account_id)
        )
    )
    if transfer_count.scalar_one() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an account with transfer history. Archive it instead.",
        )

    await db.delete(account)
    await db.commit()
