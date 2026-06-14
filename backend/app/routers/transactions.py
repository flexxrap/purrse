import logging
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionList,
    TransactionOut,
    TransactionUpdate,
)
from app.services import transaction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.create(
        user_id=current_user.id,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        tx_date=body.tx_date,
        note=body.note,
        db=db,
    )


@router.get("", response_model=TransactionList)
async def list_transactions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    type: Literal["income", "expense"] | None = Query(None),
    cursor: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, next_cursor = await transaction_service.list_transactions(
        user_id=current_user.id,
        db=db,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        type_filter=type,
        cursor=cursor,
        limit=limit,
    )
    return TransactionList(items=items, next_cursor=next_cursor)


@router.patch("/{tx_id}", response_model=TransactionOut)
async def update_transaction(
    tx_id: uuid.UUID,
    body: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.update(
        tx_id=tx_id,
        user_id=current_user.id,
        db=db,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        tx_date=body.tx_date,
        note=body.note,
    )


@router.delete("/{tx_id}")
async def delete_transaction(
    tx_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await transaction_service.soft_delete(
        tx_id=tx_id,
        user_id=current_user.id,
        db=db,
    )
    return {"ok": True}
