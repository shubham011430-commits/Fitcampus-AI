from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.database import get_db
from app.models import User, Activity
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.utils.security import get_current_user
from app.utils.helpers import today_str, estimate_calories, points_for_activity
from app.services.streak_service import update_streak

router = APIRouter(prefix="/api/activities", tags=["activities"])

MIN_SECONDS_BEFORE_COMPLETE = 60  # anti points-farming


def _to_response(a: Activity) -> dict:
    return {
        "id": a.id, "activity_type": a.activity_type,
        "duration_minutes": a.duration_minutes,
        "calories_estimate": a.calories_estimate or 0,
        "status": a.status, "date": a.date, "points_earned": a.points_earned or 0,
    }


@router.get("/today", response_model=list[ActivityResponse])
async def today_activities(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity).where(Activity.user_id == user.id, Activity.date == today_str()))
    return [_to_response(a) for a in result.scalars().all()]


@router.get("/history", response_model=list[ActivityResponse])
async def activity_history(limit: int = 30, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(Activity).where(Activity.user_id == user.id)
        .order_by(Activity.date.desc(), Activity.id.desc()).limit(limit)
    )
    return [_to_response(a) for a in result.scalars().all()]


@router.post("", response_model=ActivityResponse)
async def create_activity(req: ActivityCreate, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    cal = req.calories_estimate or estimate_calories(req.activity_type, req.duration_minutes)
    act = Activity(
        user_id=user.id, activity_type=req.activity_type,
        duration_minutes=req.duration_minutes, calories_estimate=cal,
        status="pending", date=today_str(), points_earned=0,
        created_at=datetime.utcnow(),
    )
    db.add(act)
    await db.commit()
    await db.refresh(act)
    return _to_response(act)


@router.post("/{activity_id}/complete", response_model=ActivityResponse)
async def complete_activity(activity_id: int, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity).where(Activity.id == activity_id, Activity.user_id == user.id))
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(404, "Activity not found")
    if act.status == "completed":
        return _to_response(act)

    elapsed = (datetime.utcnow() - act.created_at).total_seconds()
    if elapsed < MIN_SECONDS_BEFORE_COMPLETE:
        raise HTTPException(400, "Keep going! You can complete this after at least 1 minute.")

    pts = points_for_activity(act.duration_minutes)
    await db.execute(update(Activity).where(Activity.id == activity_id).values(status="completed", points_earned=pts))
    await db.execute(update(User).where(User.id == user.id).values(points=User.points + pts))
    await db.commit()
    await update_streak(db, user.id, today_str())

    act.status = "completed"
    act.points_earned = pts
    return _to_response(act)
