import logging
import math
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.goal import Goal
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


async def _avg_monthly_free_balance(user_id: uuid.UUID, db: AsyncSession) -> int:
    """
    Returns average monthly (income - expense) over the last 3 complete months.
    Used to estimate months_to_completion for goals.
    Returns 0 if no data or balance is non-positive.
    """
    from datetime import date

    today = datetime.now(timezone.utc).date()
    # Look back 3 months from start of current month
    if today.month > 3:
        since = date(today.year, today.month - 3, 1)
    else:
        since = date(today.year - 1, today.month + 9, 1)

    result = await db.execute(
        select(
            func.sum(Transaction.amount_cents).label("total"),
            Category.type.label("type"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.deleted_at.is_(None))
        .where(Transaction.tx_date >= since)
        .where(Transaction.tx_date < date(today.year, today.month, 1))
        .group_by(Category.type)
    )
    rows = result.all()
    totals = {row.type: row.total or 0 for row in rows}
    free = totals.get("income", 0) - totals.get("expense", 0)
    if free <= 0:
        return 0
    return free // 3  # average per month


async def _enrich_goal(goal: Goal, monthly_free: int) -> dict:
    remaining = goal.target_cents - goal.current_cents
    if monthly_free > 0 and remaining > 0:
        months = math.ceil(remaining / monthly_free)
    else:
        months = None
    data = {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "target_cents": goal.target_cents,
        "current_cents": goal.current_cents,
        "deadline": goal.deadline,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "months_to_completion": months,
    }
    return data


async def get_all(user_id: uuid.UUID, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at)
    )
    goals = list(result.scalars().all())
    monthly_free = await _avg_monthly_free_balance(user_id, db)
    return [await _enrich_goal(g, monthly_free) for g in goals]


async def create(
    user_id: uuid.UUID,
    name: str,
    target_cents: int,
    current_cents: int,
    deadline,
    db: AsyncSession,
) -> dict:
    goal = Goal(
        user_id=user_id,
        name=name,
        target_cents=target_cents,
        current_cents=current_cents,
        deadline=deadline,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    monthly_free = await _avg_monthly_free_balance(user_id, db)
    return await _enrich_goal(goal, monthly_free)


async def update(
    goal_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
    name: str | None = None,
    target_cents: int | None = None,
    current_cents: int | None = None,
    deadline=None,
) -> dict:
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    if name is not None:
        goal.name = name
    if target_cents is not None:
        goal.target_cents = target_cents
    if current_cents is not None:
        goal.current_cents = current_cents
    if deadline is not None:
        goal.deadline = deadline

    goal.updated_at = datetime.utcnow()
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    monthly_free = await _avg_monthly_free_balance(user_id, db)
    return await _enrich_goal(goal, monthly_free)


async def delete(goal_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    await db.delete(goal)
    await db.commit()
