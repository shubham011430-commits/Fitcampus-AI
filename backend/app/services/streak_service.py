from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.models import User


async def update_streak(db: AsyncSession, user_id: int, activity_date: str):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    last = user.last_activity_date
    current = user.current_streak or 0
    longest = user.longest_streak or 0

    if last == activity_date:
        return {"current_streak": current, "longest_streak": longest}

    if last:
        gap = (date.fromisoformat(activity_date) - date.fromisoformat(last)).days
        current = current + 1 if gap == 1 else 1
    else:
        current = 1

    longest = max(longest, current)
    await db.execute(
        update(User).where(User.id == user_id)
        .values(current_streak=current, longest_streak=longest, last_activity_date=activity_date)
    )
    await db.commit()
    return {"current_streak": current, "longest_streak": longest}


async def compute_rank(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(User.points).where(User.id == user_id))
    points = result.scalar() or 0
    result = await db.execute(select(func.count(User.id)).where(User.points > points))
    return (result.scalar() or 0) + 1
