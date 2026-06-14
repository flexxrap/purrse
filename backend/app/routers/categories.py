import logging
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import category_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
@limiter.limit("300/minute")
async def list_categories(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.get_all(user_id=current_user.id, db=db)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_category(
    body: CategoryCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.create(
        user_id=current_user.id,
        name=body.name,
        color=body.color,
        type_=body.type,
        db=db,
    )


@router.patch("/{category_id}", response_model=CategoryOut)
@limiter.limit("300/minute")
async def update_category(
    category_id: uuid.UUID,
    body: CategoryUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await category_service.update(
        category_id=category_id,
        user_id=current_user.id,
        name=body.name,
        color=body.color,
        type_=body.type,
        db=db,
    )


@router.delete("/{category_id}")
@limiter.limit("300/minute")
async def delete_category(
    category_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await category_service.delete(
        category_id=category_id,
        user_id=current_user.id,
        db=db,
    )
    return {"ok": True}
