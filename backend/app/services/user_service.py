import logging
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.user import UpdateMeRequest
from app.services.auth_service import hash_password, verify_password

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


async def update_me(user: User, data: UpdateMeRequest, db: AsyncSession) -> User:
    if data.email is not None and data.email != user.email:
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = data.email

    if data.currency is not None:
        user.currency = data.currency.upper()

    user.updated_at = datetime.utcnow()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def export_user_data(user: User, db: AsyncSession) -> dict:
    txs = (
        await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(Transaction.tx_date.desc())
        )
    ).scalars().all()

    cats = (
        await db.execute(select(Category).where(Category.user_id == user.id))
    ).scalars().all()

    goals = (
        await db.execute(select(Goal).where(Goal.user_id == user.id))
    ).scalars().all()

    budgets = (
        await db.execute(select(Budget).where(Budget.user_id == user.id))
    ).scalars().all()

    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "telegram_id": user.telegram_id,
            "currency": user.currency,
            "created_at": user.created_at.isoformat(),
        },
        "transactions": [
            {
                "id": str(t.id),
                "category_id": str(t.category_id) if t.category_id else None,
                "amount_cents": t.amount_cents,
                "note": t.note,
                "tx_date": t.tx_date.isoformat(),
                "created_at": t.created_at.isoformat(),
                "deleted_at": t.deleted_at.isoformat() if t.deleted_at else None,
            }
            for t in txs
        ],
        "categories": [
            {
                "id": str(c.id),
                "name": c.name,
                "color": c.color,
                "type": c.type,
                "created_at": c.created_at.isoformat(),
            }
            for c in cats
        ],
        "goals": [
            {
                "id": str(g.id),
                "name": g.name,
                "target_cents": g.target_cents,
                "current_cents": g.current_cents,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "created_at": g.created_at.isoformat(),
            }
            for g in goals
        ],
        "budgets": [
            {
                "id": str(b.id),
                "category_id": str(b.category_id),
                "month": b.month,
                "limit_cents": b.limit_cents,
                "created_at": b.created_at.isoformat(),
            }
            for b in budgets
        ],
    }


async def delete_account(user: User, db: AsyncSession) -> None:
    for model in (Transaction, Budget, Goal, Category):
        await db.execute(delete(model).where(model.user_id == user.id))
    await db.delete(user)
    await db.commit()


async def change_password(
    user: User,
    old_password: str,
    new_password: str,
    db: AsyncSession,
) -> None:
    if user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for Telegram-only account",
        )
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.add(user)
    await db.commit()
