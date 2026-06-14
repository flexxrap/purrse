import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recurring import RecurringTransaction
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def _advance_date(current: date, frequency: str) -> date:
    if frequency == "weekly":
        return current + timedelta(weeks=1)
    if frequency == "monthly":
        return current + relativedelta(months=1)
    return current + relativedelta(years=1)


async def list_all(user_id: uuid.UUID, db: AsyncSession) -> list[RecurringTransaction]:
    result = await db.execute(
        select(RecurringTransaction)
        .where(RecurringTransaction.user_id == user_id)
        .order_by(RecurringTransaction.created_at.desc())
    )
    return list(result.scalars().all())


async def create(
    user_id: uuid.UUID,
    amount_cents: int,
    category_id: uuid.UUID | None,
    note: str | None,
    frequency: str,
    start_date: date,
    db: AsyncSession,
) -> RecurringTransaction:
    rt = RecurringTransaction(
        user_id=user_id,
        category_id=category_id,
        amount_cents=amount_cents,
        note=note,
        frequency=frequency,
        next_date=start_date,
    )
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return rt


async def update(
    rt_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    amount_cents: int | None = None,
    category_id: uuid.UUID | None = None,
    note: str | None = None,
    frequency: str | None = None,
    is_active: bool | None = None,
) -> RecurringTransaction:
    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.id == rt_id,
            RecurringTransaction.user_id == user_id,
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found"
        )

    if amount_cents is not None:
        rt.amount_cents = amount_cents
    if category_id is not None:
        rt.category_id = category_id
    if note is not None:
        rt.note = note
    if frequency is not None:
        rt.frequency = frequency
    if is_active is not None:
        rt.is_active = is_active

    rt.updated_at = datetime.now(timezone.utc)
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return rt


async def delete(rt_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.id == rt_id,
            RecurringTransaction.user_id == user_id,
        )
    )
    rt = result.scalar_one_or_none()
    if rt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recurring transaction not found"
        )
    await db.delete(rt)
    await db.commit()


async def process_due(db: AsyncSession) -> int:
    """Create transactions for all active recurring entries due today or earlier."""
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(RecurringTransaction).where(
            RecurringTransaction.is_active.is_(True),
            RecurringTransaction.next_date <= today,
        )
    )
    due = list(result.scalars().all())
    created = 0
    now = datetime.now(timezone.utc)
    for rt in due:
        # May need to create multiple transactions if missed several periods
        current = rt.next_date
        while current <= today:
            tx = Transaction(
                user_id=rt.user_id,
                category_id=rt.category_id,
                amount_cents=rt.amount_cents,
                note=rt.note,
                tx_date=current,
                created_at=now,
                updated_at=now,
            )
            db.add(tx)
            created += 1
            current = _advance_date(current, rt.frequency)
        rt.next_date = current
        rt.updated_at = now
        db.add(rt)
    if due:
        await db.commit()
    logger.info("Recurring: created %d transactions", created)
    return created
