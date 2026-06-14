import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.budget import BudgetBarItem
from app.services.telegram_service import send_message

logger = logging.getLogger(__name__)


async def upsert(
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    month: str,
    limit_cents: int,
    db: AsyncSession,
) -> Budget:
    # Verify category belongs to user
    cat = await db.get(Category, category_id)
    if cat is None or cat.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    stmt = (
        insert(Budget)
        .values(
            user_id=user_id,
            category_id=category_id,
            month=month,
            limit_cents=limit_cents,
            updated_at=datetime.utcnow(),
        )
        .on_conflict_do_update(
            constraint="uq_budgets_user_category_month",
            set_={"limit_cents": limit_cents, "updated_at": datetime.utcnow()},
        )
        .returning(Budget)
    )
    result = await db.execute(stmt)
    await db.commit()
    row = result.fetchone()
    return row[0]


async def list_budgets(user_id: uuid.UUID, month: str, db: AsyncSession) -> list[Budget]:
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == user_id, Budget.month == month)
        .order_by(Budget.category_id)
    )
    return list(result.scalars().all())


async def delete(user_id: uuid.UUID, budget_id: uuid.UUID, db: AsyncSession) -> None:
    budget = await db.get(Budget, budget_id)
    if budget is None or budget.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    await db.delete(budget)
    await db.commit()


async def budget_bars(
    user_id: uuid.UUID,
    month: str,
    db: AsyncSession,
) -> list[BudgetBarItem]:
    year, mon = int(month[:4]), int(month[5:])

    # Fetch budgets with category info
    result = await db.execute(
        select(Budget, Category)
        .join(Category, Budget.category_id == Category.id)
        .where(Budget.user_id == user_id, Budget.month == month)
    )
    rows = result.all()
    if not rows:
        return []

    # Fetch actuals for these categories in this month
    cat_ids = [r.Budget.category_id for r in rows]
    actuals_result = await db.execute(
        select(Transaction.category_id, func.sum(Transaction.amount_cents).label("total"))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.category_id.in_(cat_ids),
            func.extract("year", Transaction.tx_date) == year,
            func.extract("month", Transaction.tx_date) == mon,
        )
        .group_by(Transaction.category_id)
    )
    actuals = {str(r.category_id): r.total for r in actuals_result.all()}

    items = []
    for row in rows:
        b, cat = row.Budget, row.Category
        actual = actuals.get(str(b.category_id), 0)
        pct = min(round(actual / b.limit_cents * 100), 999) if b.limit_cents else 0
        items.append(BudgetBarItem(
            category_id=b.category_id,
            name=cat.name,
            color=cat.color,
            limit_cents=b.limit_cents,
            actual_cents=actual,
            pct=pct,
        ))

    return sorted(items, key=lambda x: x.pct, reverse=True)


async def check_and_alert(
    user_id: uuid.UUID,
    telegram_id: int | None,
    category_id: uuid.UUID,
    month: str,
    db: AsyncSession,
) -> None:
    """Send a Telegram alert if spending has crossed 80% of the budget for this category/month."""
    if telegram_id is None:
        return

    # Find budget that hasn't already triggered an alert
    result = await db.execute(
        select(Budget).where(
            Budget.user_id == user_id,
            Budget.category_id == category_id,
            Budget.month == month,
            Budget.alert_80_sent.is_(False),
        )
    )
    budget = result.scalar_one_or_none()
    if budget is None:
        return

    # Only alert for expense categories
    cat_result = await db.execute(
        select(Category).where(Category.id == category_id, Category.user_id == user_id)
    )
    cat = cat_result.scalar_one_or_none()
    if cat is None or cat.type != "expense":
        return

    year, mon = int(month[:4]), int(month[5:])
    actual_result = await db.execute(
        select(func.sum(Transaction.amount_cents)).where(
            Transaction.user_id == user_id,
            Transaction.category_id == category_id,
            Transaction.deleted_at.is_(None),
            func.extract("year", Transaction.tx_date) == year,
            func.extract("month", Transaction.tx_date) == mon,
        )
    )
    actual = actual_result.scalar_one_or_none() or 0

    if actual < budget.limit_cents * 0.8:
        return

    pct = round(actual / budget.limit_cents * 100)
    budget.alert_80_sent = True
    db.add(budget)
    await db.commit()

    await send_message(
        telegram_id,
        f"⚠️ Budget alert: {cat.name} — {pct}% used for {month} "
        f"({actual // 100} / {budget.limit_cents // 100})",
    )
