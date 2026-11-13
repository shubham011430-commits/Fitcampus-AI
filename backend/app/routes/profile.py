from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from app.database import get_db
from app.models import User
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/profile", tags=["profile"])


async def _compute_rank(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(User.points).where(User.id == user_id))
    points = result.scalar() or 0
    result = await db.execute(select(func.count(User.id)).where(User.points > points))
    return (result.scalar() or 0) + 1


def _to_response(u: User, rank: int) -> ProfileResponse:
    return ProfileResponse(
        id=u.id, name=u.name, email=u.email, student_type=u.student_type or "day_scholar",
        age=u.age, weight=u.weight, height=u.height,
        body_type=u.body_type, fitness_level=u.fitness_level,
        activity_level=u.activity_level, fitness_goal=u.fitness_goal,
        dietary_preference=u.dietary_preference, allergies=u.allergies or [],
        points=u.points, current_streak=u.current_streak,
        longest_streak=u.longest_streak, last_activity_date=u.last_activity_date,
        rank=rank,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rank = await _compute_rank(db, user.id)
    return _to_response(user, rank)


@router.put("", response_model=ProfileResponse)
async def update_profile(req: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if updates:
        await db.execute(update(User).where(User.id == user.id).values(**updates))
        await db.commit()
        await db.refresh(user)
    rank = await _compute_rank(db, user.id)
    return _to_response(user, rank)