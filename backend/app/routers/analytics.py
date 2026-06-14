import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _parse_month(month_str: str | None) -> tuple[int, int]:
    """Parse 'YYYY-MM' string, defaulting to current month."""
    if month_str is None:
        now = datetime.now(timezone.utc)
        return now.year, now.month
    try:
        parts = month_str.split("-")
        if len(parts) != 2:
            raise ValueError
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must be in YYYY-MM format",
        )


@router.get("/summary")
async def get_summary(
    month: str | None = Query(None, description="YYYY-MM, default current month"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    year, mon = _parse_month(month)
    return await analytics_service.summary(
        user_id=current_user.id, year=year, month=mon, db=db
    )


@router.get("/categories")
async def get_category_breakdown(
    month: str | None = Query(None, description="YYYY-MM, default current month"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    year, mon = _parse_month(month)
    return await analytics_service.category_breakdown(
        user_id=current_user.id, year=year, month=mon, db=db
    )


@router.get("/trend")
async def get_trend(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await analytics_service.trend(
        user_id=current_user.id, months=months, db=db
    )
