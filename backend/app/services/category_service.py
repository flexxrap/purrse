import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category

logger = logging.getLogger(__name__)

MAX_CATEGORIES_PER_USER = 50


async def get_all(user_id: uuid.UUID, db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category)
        .where(Category.user_id == user_id)
        .order_by(Category.created_at)
    )
    return list(result.scalars().all())


async def create(
    user_id: uuid.UUID,
    name: str,
    color: str,
    type_: str,
    db: AsyncSession,
) -> Category:
    count_result = await db.execute(
        select(func.count()).select_from(Category).where(Category.user_id == user_id)
    )
    if count_result.scalar_one() >= MAX_CATEGORIES_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 categories reached",
        )

    category = Category(user_id=user_id, name=name, color=color, type=type_)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def update(
    category_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str | None,
    color: str | None,
    type_: str | None,
    db: AsyncSession,
) -> Category:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    if name is not None:
        category.name = name
    if color is not None:
        category.color = color
    if type_ is not None:
        category.type = type_

    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def delete(
    category_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    await db.delete(category)
    await db.commit()
