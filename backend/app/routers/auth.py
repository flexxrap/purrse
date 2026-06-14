import logging

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import (
    REFRESH_TOKEN_EXPIRE_DAYS,
    login,
    logout,
    refresh_session,
    register,
    telegram_login,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


class TelegramAuthRequest(BaseModel):
    init_data: str


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=_REFRESH_COOKIE_MAX_AGE,
        path="/auth/refresh",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key="refresh_token", path="/auth/refresh")


@router.post("/register", response_model=TokenResponse)
@limiter.limit("60/minute")
async def register_user(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, raw_refresh = await register(
        email=body.email,
        password=body.password,
        db=db,
        request=request,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token, user=user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("60/minute")
async def login_user(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, raw_refresh = await login(
        email=body.email,
        password=body.password,
        db=db,
        request=request,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token, user=user)


@router.post("/telegram", response_model=TokenResponse)
@limiter.limit("60/minute")
async def telegram_auth(
    body: TelegramAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, access_token, raw_refresh = await telegram_login(
        init_data=body.init_data,
        db=db,
        request=request,
    )
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(access_token=access_token, user=user)


@router.post("/refresh")
async def refresh_token(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
):
    if not refresh_token:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    _user, access_token, raw_new = await refresh_session(
        raw_token=refresh_token,
        db=db,
    )
    _set_refresh_cookie(response, raw_new)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_token: str | None = Cookie(default=None),
):
    await logout(
        raw_token=refresh_token,
        user_id=str(current_user.id),
        db=db,
        request=request,
    )
    _clear_refresh_cookie(response)
    return {"ok": True}
