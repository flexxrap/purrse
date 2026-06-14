import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash_to_store)."""
    raw = secrets.token_hex(64)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


async def _write_audit(
    db: AsyncSession,
    action: str,
    user_id: str | None,
    request: Request,
) -> None:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    db.add(AuditLog(user_id=user_id, action=action, ip_address=ip, user_agent=ua))


async def register(
    email: str,
    password: str,
    db: AsyncSession,
    request: Request,
) -> tuple[User, str, str]:
    """
    Creates a new user. Returns (user, access_token, raw_refresh_token).
    Raises HTTP 400 if email already exists.
    """
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    await db.flush()  # populate user.id before creating dependent rows

    raw_token, token_hash = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))

    await _write_audit(db, "register", str(user.id), request)

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id))
    return user, access_token, raw_token
