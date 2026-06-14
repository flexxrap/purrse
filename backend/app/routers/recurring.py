import logging
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.recurring import RecurringCreate, RecurringOut, RecurringUpdate
from app.services import recurring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recurring", tags=["recurring"])


@router.get("", response_model=list[RecurringOut])
async def list_recurring(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await recurring_service.list_all(current_user.id, db)


@router.post("", response_model=RecurringOut, status_code=status.HTTP_201_CREATED)
async def create_recurring(
    body: RecurringCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await recurring_service.create(
        user_id=current_user.id,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        note=body.note,
        frequency=body.frequency,
        start_date=body.start_date,
        db=db,
    )


@router.patch("/{rt_id}", response_model=RecurringOut)
async def update_recurring(
    rt_id: uuid.UUID,
    body: RecurringUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await recurring_service.update(
        rt_id=rt_id,
        user_id=current_user.id,
        db=db,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        note=body.note,
        frequency=body.frequency,
        is_active=body.is_active,
    )


@router.delete("/{rt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring(
    rt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await recurring_service.delete(rt_id, current_user.id, db)
