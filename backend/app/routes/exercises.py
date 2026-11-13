from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime

from app.database import get_db
from app.models import User, Exercise
from app.schemas.exercise import ExerciseComplete
from app.utils.security import get_current_user
from app.ai.recommendation_engine import recommend_exercises
from app.services.streak_service import update_streak
from app.utils.helpers import today_str

router = APIRouter(prefix="/api/exercises", tags=["exercises"])

MIN_SECONDS_PER_REP = 1.0
MAX_POINTS_PER_SET = 30
DAILY_POINT_CAP = 300


@router.get("")
async def list_exercises(user: User = Depends(get_current_user)):
    return recommend_exercises({"fitness_level": user.fitness_level})


@router.post("/complete")
async def complete_exercise(req: ExerciseComplete, user: User = Depends(get_current_user),
                            db: AsyncSession = Depends(get_db)):
    if req.repetitions > 0 and req.duration_seconds < req.repetitions * MIN_SECONDS_PER_REP:
        raise HTTPException(400, "Duration too short for that many repetitions")

    day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    earned_today = (await db.execute(
        select(func.coalesce(func.sum(Exercise.points_earned), 0))
        .where(Exercise.user_id == user.id, Exercise.completed_at >= day_start)
    )).scalar() or 0
    remaining = max(0, DAILY_POINT_CAP - int(earned_today))

    raw = max(5, int(req.form_score / 10) + req.repetitions // 5)
    pts = min(raw, MAX_POINTS_PER_SET, remaining)

    db.add(Exercise(
        user_id=user.id, exercise_name=req.exercise_name,
        repetitions=req.repetitions, duration=req.duration_seconds,
        form_score=req.form_score, points_earned=pts,
        completed_at=datetime.utcnow(),
    ))
    if pts:
        await db.execute(update(User).where(User.id == user.id).values(points=User.points + pts))
    await db.commit()
    await update_streak(db, user.id, today_str())
    return {"ok": True, "points_earned": pts, "daily_cap_reached": remaining - pts <= 0}
