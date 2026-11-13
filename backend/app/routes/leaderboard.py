from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("")
async def leaderboard(period: str = Query("weekly", pattern="^(weekly|monthly|all)$"),
                      user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # NOTE: period is accepted for the UI, but ranking currently uses total points.
    result = await db.execute(select(User).order_by(User.points.desc(), User.id).limit(50))
    rows, me = [], None
    for i, u in enumerate(result.scalars().all(), 1):
        entry = {"rank": i, "id": u.id, "name": u.name, "points": u.points,
                 "streak": u.current_streak, "is_me": u.id == user.id}
        rows.append(entry)
        if entry["is_me"]:
            me = entry
    return {"period": period, "entries": rows, "me": me}
