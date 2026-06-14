import csv
import io
import logging
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
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


@router.get("/export/csv")
async def export_csv(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await transaction_service.export_all(
        user_id=current_user.id,
        db=db,
        date_from=date_from,
        date_to=date_to,
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Category", "Type", "Amount", "Note"])
    for r in rows:
        writer.writerow([
            r.tx_date.isoformat(),
            r.category_name or "",
            r.category_type or "",
            f"{r.amount_cents / 100:.2f}",
            r.note or "",
        ])
    buf.seek(0)
    df = date_from.isoformat() if date_from else "all"
    dt = date_to.isoformat() if date_to else "all"
    filename = f"transactions_{df}_{dt}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_transaction(
    body: TransactionCreate,
    request: Request,
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
@limiter.limit("300/minute")
async def list_transactions(
    request: Request,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    type: Literal["income", "expense"] | None = Query(None),
    search: str | None = Query(None, min_length=3, max_length=200),
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
        search=search,
        cursor=cursor,
        limit=limit,
    )
    return TransactionList(items=items, next_cursor=next_cursor)


@router.patch("/{tx_id}", response_model=TransactionOut)
@limiter.limit("300/minute")
async def update_transaction(
    tx_id: uuid.UUID,
    body: TransactionUpdate,
    request: Request,
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
@limiter.limit("300/minute")
async def delete_transaction(
    tx_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await transaction_service.soft_delete(
        tx_id=tx_id,
        user_id=current_user.id,
        db=db,
    )
    return {"ok": True}
