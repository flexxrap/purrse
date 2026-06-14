import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transfer import Transfer
from app.services import account_service


async def list_all(user_id: uuid.UUID, db: AsyncSession) -> list[Transfer]:
    result = await db.execute(
        select(Transfer)
        .where(Transfer.user_id == user_id)
        .order_by(Transfer.tx_date.desc(), Transfer.created_at.desc())
    )
    return list(result.scalars().all())


async def create(
    user_id: uuid.UUID,
    from_account_id: uuid.UUID,
    to_account_id: uuid.UUID,
    amount_cents: int,
    tx_date: date,
    note: str | None,
    db: AsyncSession,
) -> Transfer:
    # Verify both accounts exist and belong to this user
    await account_service.get_one(from_account_id, user_id, db)
    await account_service.get_one(to_account_id, user_id, db)

    transfer = Transfer(
        user_id=user_id,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
        amount_cents=amount_cents,
        tx_date=tx_date,
        note=note,
    )
    db.add(transfer)
    await db.commit()
    await db.refresh(transfer)
    return transfer
