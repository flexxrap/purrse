import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    category_id: uuid.UUID
    tx_date: date
    note: str | None = Field(None, max_length=500)


class TransactionUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    amount_cents: int | None = Field(None, gt=0)
    category_id: uuid.UUID | None = None
    tx_date: date | None = None
    note: str | None = Field(None, max_length=500)


class TransactionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    amount_cents: int
    note: str | None
    tx_date: date
    created_at: datetime
    updated_at: datetime


class TransactionList(BaseModel):
    items: list[TransactionOut]
    next_cursor: uuid.UUID | None


class ImportPreviewOut(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    total_rows: int


class ImportMapping(BaseModel):
    date_col: int = Field(ge=0)
    amount_col: int = Field(ge=0)
    category_col: int | None = None
    note_col: int | None = None


class ImportConfirmOut(BaseModel):
    created: int
    skipped: int
