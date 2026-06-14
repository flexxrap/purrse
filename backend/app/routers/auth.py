import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.user import RegisterRequest, TokenResponse
from app.services.auth_service import REFRESH_TOKEN_EXPIRE_DAYS, register

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


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


@router.post("/register", response_model=TokenResponse)
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
