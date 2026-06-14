import logging
import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.limiter import limiter
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalOut, GoalUpdate
from app.services import goal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("", response_model=list[GoalOut])
@limiter.limit("300/minute")
async def list_goals(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await goal_service.get_all(user_id=current_user.id, db=db)


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("300/minute")
async def create_goal(
    body: GoalCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await goal_service.create(
        user_id=current_user.id,
        name=body.name,
        target_cents=body.target_cents,
        current_cents=body.current_cents,
        deadline=body.deadline,
        db=db,
    )


@router.patch("/{goal_id}", response_model=GoalOut)
@limiter.limit("300/minute")
async def update_goal(
    goal_id: uuid.UUID,
    body: GoalUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await goal_service.update(
        goal_id=goal_id,
        user_id=current_user.id,
        db=db,
        name=body.name,
        target_cents=body.target_cents,
        current_cents=body.current_cents,
        deadline=body.deadline,
    )


@router.delete("/{goal_id}")
@limiter.limit("300/minute")
async def delete_goal(
    goal_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await goal_service.delete(goal_id=goal_id, user_id=current_user.id, db=db)
    return {"ok": True}
