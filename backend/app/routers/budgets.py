import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.budget import BudgetOut, BudgetUpsert
from app.services import budget_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetOut])
async def list_budgets(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await budget_service.list_budgets(
        user_id=current_user.id, month=month, db=db
    )


@router.post("", response_model=BudgetOut)
async def upsert_budget(
    body: BudgetUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await budget_service.upsert(
        user_id=current_user.id,
        category_id=body.category_id,
        month=body.month,
        limit_cents=body.limit_cents,
        db=db,
    )


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await budget_service.delete(
        user_id=current_user.id, budget_id=budget_id, db=db
    )
