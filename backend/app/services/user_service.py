import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UpdateMeRequest
from app.services.auth_service import hash_password, verify_password

logger = logging.getLogger(__name__)


async def update_me(user: User, data: UpdateMeRequest, db: AsyncSession) -> User:
    if data.email is not None and data.email != user.email:
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use",
            )
        user.email = data.email

    if data.currency is not None:
        user.currency = data.currency.upper()

    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    user: User,
    old_password: str,
    new_password: str,
    db: AsyncSession,
) -> None:
    if user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for Telegram-only account",
        )
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
