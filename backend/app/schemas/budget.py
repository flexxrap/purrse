import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BudgetUpsert(BaseModel):
    category_id: uuid.UUID
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    limit_cents: int = Field(gt=0)


class BudgetOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    category_id: uuid.UUID
    month: str
    limit_cents: int
    updated_at: datetime


class BudgetBarItem(BaseModel):
    category_id: uuid.UUID
    name: str
    color: str
    limit_cents: int
    actual_cents: int
    pct: int
