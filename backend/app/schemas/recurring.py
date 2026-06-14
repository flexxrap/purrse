import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecurringCreate(BaseModel):
    account_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    category_id: uuid.UUID | None = None
    note: str | None = Field(None, max_length=500)
    frequency: Literal["weekly", "monthly", "yearly"]
    start_date: date


class RecurringUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    amount_cents: int | None = Field(None, gt=0)
    category_id: uuid.UUID | None = None
    note: str | None = Field(None, max_length=500)
    frequency: Literal["weekly", "monthly", "yearly"] | None = None
    is_active: bool | None = None


class RecurringOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    amount_cents: int
    note: str | None
    frequency: str
    next_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime
