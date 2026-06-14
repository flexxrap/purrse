import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, unquote

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


async def _issue_tokens(
    user: User,
    db: AsyncSession,
) -> tuple[str, str]:
    """Creates a new refresh token row and returns (access_token, raw_refresh_token)."""
    raw_token, token_hash = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
    return create_access_token(str(user.id)), raw_token


async def login(
    email: str,
    password: str,
    db: AsyncSession,
    request: Request,
) -> tuple[User, str, str]:
    """
    Verifies credentials. Returns (user, access_token, raw_refresh_token).
    Raises HTTP 401 on bad credentials. Writes audit_log on both success and failure.
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    bad_creds = user is None or user.password_hash is None
    if bad_creds or not verify_password(password, user.password_hash):  # type: ignore[arg-type]
        # Still write audit even on failure (user_id may be None if user not found)
        failed_uid = str(user.id) if user else None
        await _write_audit(db, "failed_login", failed_uid, request)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    access_token, raw_token = await _issue_tokens(user, db)
    await _write_audit(db, "login", str(user.id), request)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_token


async def refresh_session(
    raw_token: str,
    db: AsyncSession,
) -> tuple[User, str, str]:
    """
    Validates a refresh token, revokes it, and issues a new one (rotation).
    Returns (user, new_access_token, new_raw_refresh_token).
    Raises HTTP 401 if token is missing, revoked, or expired.
    """
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if (
        token_row is None
        or token_row.revoked
        or token_row.expires_at.replace(tzinfo=timezone.utc) < now
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old token
    token_row.revoked = True
    db.add(token_row)

    user = await db.get(User, token_row.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token, raw_new_token = await _issue_tokens(user, db)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_new_token


async def logout(
    raw_token: str | None,
    user_id: str,
    db: AsyncSession,
    request: Request,
) -> None:
    """Revokes the refresh token (if present) and writes audit_log."""
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
        )
        token_row = result.scalar_one_or_none()
        if token_row:
            token_row.revoked = True
            db.add(token_row)

    await _write_audit(db, "logout", user_id, request)
    await db.commit()


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    """
    Verifies Telegram WebApp initData HMAC-SHA256 signature.
    Raises ValueError on invalid hash or expired auth_date (>86400s).
    Returns the parsed user dict from initData.
    """
    parsed = dict(parse_qs(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", [None])[0]
    if not received_hash:
        raise ValueError("No hash in initData")

    auth_date = int(parsed.get("auth_date", [0])[0])
    if time.time() - auth_date > 86400:
        raise ValueError("initData expired")

    data_check_string = "\n".join(
        f"{k}={unquote(v[0])}"
        for k, v in sorted(parsed.items())
    )
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("Invalid hash")

    return json.loads(unquote(parsed["user"][0]))


async def telegram_login(
    init_data: str,
    db: AsyncSession,
    request: Request,
) -> tuple[User, str, str]:
    """
    Verifies Telegram initData, upserts user by telegram_id, issues tokens.
    Returns (user, access_token, raw_refresh_token).
    Raises HTTP 400 on invalid or expired initData.
    """
    try:
        tg_user = verify_telegram_init_data(init_data, settings.BOT_TOKEN)
    except ValueError as exc:
        detail = "initData expired" if "expired" in str(exc) else "Invalid initData"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    telegram_id: int = int(tg_user["id"])

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(telegram_id=telegram_id)
        db.add(user)
        await db.flush()

    access_token, raw_token = await _issue_tokens(user, db)
    await _write_audit(db, "telegram_login", str(user.id), request)
    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_token


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

    access_token, raw_token = await _issue_tokens(user, db)
    await _write_audit(db, "register", str(user.id), request)

    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_token
