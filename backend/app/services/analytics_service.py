import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    """Returns (first_day, last_day) for the given year/month."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


async def summary(
    user_id: uuid.UUID,
    year: int,
    month: int,
    db: AsyncSession,
) -> dict:
    date_from, date_to = _month_bounds(year, month)

    result = await db.execute(
        select(
            func.sum(Transaction.amount_cents).label("total"),
            Category.type.label("type"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.deleted_at.is_(None))
        .where(Transaction.tx_date >= date_from)
        .where(Transaction.tx_date <= date_to)
        .group_by(Category.type)
    )
    rows = result.all()
    totals = {row.type: row.total or 0 for row in rows}
    income = totals.get("income", 0)
    expense = totals.get("expense", 0)
    return {
        "month": f"{year:04d}-{month:02d}",
        "income_cents": income,
        "expense_cents": expense,
        "balance_cents": income - expense,
    }


async def category_breakdown(
    user_id: uuid.UUID,
    year: int,
    month: int,
    db: AsyncSession,
) -> dict:
    date_from, date_to = _month_bounds(year, month)

    result = await db.execute(
        select(
            Category.id.label("category_id"),
            Category.name.label("name"),
            Category.color.label("color"),
            Category.type.label("type"),
            func.sum(Transaction.amount_cents).label("total_cents"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.deleted_at.is_(None))
        .where(Transaction.tx_date >= date_from)
        .where(Transaction.tx_date <= date_to)
        .group_by(Category.id, Category.name, Category.color, Category.type)
        .order_by(func.sum(Transaction.amount_cents).desc())
    )
    rows = result.all()

    grand_total = sum(r.total_cents for r in rows)
    if grand_total == 0:
        return {"month": f"{year:04d}-{month:02d}", "items": []}

    top5 = rows[:5]
    rest = rows[5:]

    items = [
        {
            "category_id": str(r.category_id),
            "name": r.name,
            "color": r.color,
            "type": r.type,
            "total_cents": r.total_cents,
            "percentage": round(r.total_cents / grand_total * 100, 2),
        }
        for r in top5
    ]

    if rest:
        other_total = sum(r.total_cents for r in rest)
        items.append({
            "category_id": None,
            "name": "Other",
            "color": "#CCCCCC",
            "type": "expense",
            "total_cents": other_total,
            "percentage": round(other_total / grand_total * 100, 2),
        })

    return {"month": f"{year:04d}-{month:02d}", "items": items}


async def trend(
    user_id: uuid.UUID,
    months: int,
    db: AsyncSession,
) -> dict:
    today = datetime.now(timezone.utc).date()

    result = await db.execute(
        select(
            extract("year", Transaction.tx_date).label("year"),
            extract("month", Transaction.tx_date).label("month"),
            func.sum(Transaction.amount_cents).label("total"),
            Category.type.label("type"),
        )
        .join(Category, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.deleted_at.is_(None))
        .group_by(
            extract("year", Transaction.tx_date),
            extract("month", Transaction.tx_date),
            Category.type,
        )
        .order_by(
            extract("year", Transaction.tx_date),
            extract("month", Transaction.tx_date),
        )
    )
    rows = result.all()

    # Build a dict keyed by (year, month)
    data: dict[tuple[int, int], dict] = {}
    for row in rows:
        key = (int(row.year), int(row.month))
        if key not in data:
            data[key] = {"income_cents": 0, "expense_cents": 0}
        if row.type == "income":
            data[key]["income_cents"] = row.total or 0
        else:
            data[key]["expense_cents"] = row.total or 0

    # Generate the last N months in order
    items = []
    y, m = today.year, today.month
    month_keys = []
    for _ in range(months):
        month_keys.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    month_keys.reverse()  # oldest → newest

    for y, m in month_keys:
        d = data.get((y, m), {"income_cents": 0, "expense_cents": 0})
        items.append({
            "month": f"{y:04d}-{m:02d}",
            "income_cents": d["income_cents"],
            "expense_cents": d["expense_cents"],
        })

    return {"items": items}
