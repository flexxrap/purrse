import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(max_length=64)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    type: Literal["income", "expense"]


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=64)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    type: Literal["income", "expense"] | None = None


class CategoryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str
    type: str
    created_at: datetime
