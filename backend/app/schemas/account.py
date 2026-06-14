import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: Literal["cash", "card", "savings", "other"]
    initial_balance_cents: int = 0


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=64)
    type: Literal["cash", "card", "savings", "other"] | None = None
    initial_balance_cents: int | None = None
    is_archived: bool | None = None


class AccountOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    type: str
    initial_balance_cents: int
    balance_cents: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
