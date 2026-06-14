import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

_PAGE_SIZE_DEFAULT = 50
_PAGE_SIZE_MAX = 100


async def create(
    user_id: uuid.UUID,
    amount_cents: int,
    category_id: uuid.UUID,
    tx_date: date,
    note: str | None,
    db: AsyncSession,
) -> Transaction:
    # Verify category exists and belongs to this user
    cat_result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    if cat_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or does not belong to user",
        )

    tx = Transaction(
        user_id=user_id,
        category_id=category_id,
        amount_cents=amount_cents,
        tx_date=tx_date,
        note=note,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def list_transactions(
    user_id: uuid.UUID,
    db: AsyncSession,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: uuid.UUID | None = None,
    type_filter: str | None = None,
    cursor: uuid.UUID | None = None,
    limit: int = _PAGE_SIZE_DEFAULT,
) -> tuple[list[Transaction], uuid.UUID | None]:
    """Returns (items, next_cursor). next_cursor is None when no more pages."""
    limit = min(limit, _PAGE_SIZE_MAX)

    today = datetime.now(timezone.utc).date()
    if date_from is None:
        date_from = today - timedelta(days=30)
    if date_to is None:
        date_to = today

    query = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(Transaction.deleted_at.is_(None))
        .where(Transaction.tx_date >= date_from)
        .where(Transaction.tx_date <= date_to)
    )

    if category_id is not None:
        query = query.where(Transaction.category_id == category_id)

    if type_filter is not None:
        # Join categories to filter by type
        query = query.join(
            Category,
            Transaction.category_id == Category.id,
        ).where(Category.type == type_filter)

    if cursor is not None:
        query = query.where(Transaction.id < cursor)

    query = query.order_by(Transaction.id.desc()).limit(limit + 1)

    result = await db.execute(query)
    rows = list(result.scalars().all())

    next_cursor: uuid.UUID | None = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = rows[-1].id

    return rows, next_cursor


async def update(
    tx_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    amount_cents: int | None = None,
    category_id: uuid.UUID | None = None,
    tx_date: date | None = None,
    note: str | None = None,
) -> Transaction:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == tx_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )
    tx = result.scalar_one_or_none()
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if amount_cents is not None:
        tx.amount_cents = amount_cents
    if category_id is not None:
        tx.category_id = category_id
    if tx_date is not None:
        tx.tx_date = tx_date
    if note is not None:
        tx.note = note

    tx.updated_at = datetime.now(timezone.utc)
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


async def soft_delete(
    tx_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == tx_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )
    tx = result.scalar_one_or_none()
    if tx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    tx.deleted_at = datetime.now(timezone.utc)
    db.add(tx)
    await db.commit()
