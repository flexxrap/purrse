import csv
import io
import logging
import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.models.user import User
from app.schemas.transaction import (
    ImportConfirmOut,
    ImportMapping,
    ImportPreviewOut,
    TransactionCreate,
    TransactionList,
    TransactionOut,
    TransactionUpdate,
)
from app.services import budget_service, import_service, transaction_service
from app.services.category_service import get_all as get_all_categories

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


_MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/import/preview", response_model=ImportPreviewOut)
async def import_preview(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    if len(content) > _MAX_CSV_BYTES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    return import_service.parse_csv_preview(content)


@router.post("/import/confirm", response_model=ImportConfirmOut)
async def import_confirm(
    file: UploadFile = File(...),
    mapping: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    if len(content) > _MAX_CSV_BYTES:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")
    try:
        m = ImportMapping.model_validate_json(mapping)
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid column mapping")
    categories = await get_all_categories(current_user.id, db)
    rows, skipped = import_service.parse_csv_rows(
        content,
        date_col=m.date_col,
        amount_col=m.amount_col,
        category_col=m.category_col,
        note_col=m.note_col,
        categories=categories,
    )
    created = await transaction_service.bulk_create(current_user.id, rows, db)
    return ImportConfirmOut(created=created, skipped=skipped)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_transaction(
    body: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await transaction_service.create(
        user_id=current_user.id,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        tx_date=body.tx_date,
        note=body.note,
        db=db,
    )
    await budget_service.check_and_alert(
        user_id=current_user.id,
        telegram_id=current_user.telegram_id,
        category_id=body.category_id,
        month=body.tx_date.strftime("%Y-%m"),
        db=db,
    )
    return tx


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
    tx = await transaction_service.update(
        tx_id=tx_id,
        user_id=current_user.id,
        db=db,
        amount_cents=body.amount_cents,
        category_id=body.category_id,
        tx_date=body.tx_date,
        note=body.note,
    )
    await budget_service.check_and_alert(
        user_id=current_user.id,
        telegram_id=current_user.telegram_id,
        category_id=tx.category_id,
        month=tx.tx_date.strftime("%Y-%m"),
        db=db,
    )
    return tx


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
