import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UpdateMeRequest, UserOut
from app.services.user_service import change_password, update_me

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me_endpoint(
    body: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_me(user=current_user, data=body, db=db)


@router.post("/me/password", status_code=204)
async def change_password_endpoint(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await change_password(
        user=current_user,
        old_password=body.old_password,
        new_password=body.new_password,
        db=db,
    )
