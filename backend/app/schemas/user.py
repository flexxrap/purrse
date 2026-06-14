import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    telegram_id: int | None
    currency: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UpdateMeRequest(BaseModel):
    email: EmailStr | None = None
    currency: str | None = Field(None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)
