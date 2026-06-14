import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    name: str = Field(max_length=128)
    target_cents: int = Field(gt=0)
    current_cents: int = Field(ge=0, default=0)
    deadline: date | None = None


class GoalUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    target_cents: int | None = Field(None, gt=0)
    current_cents: int | None = Field(None, ge=0)
    deadline: date | None = None


class GoalOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    target_cents: int
    current_cents: int
    deadline: date | None
    created_at: datetime
    updated_at: datetime
    months_to_completion: int | None = None
