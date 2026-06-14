import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class TransferCreate(BaseModel):
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    tx_date: date
    note: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def check_different_accounts(self):
        if self.from_account_id == self.to_account_id:
            raise ValueError("from_account_id and to_account_id must differ")
        return self


class TransferOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    amount_cents: int
    note: str | None
    tx_date: date
    created_at: datetime
