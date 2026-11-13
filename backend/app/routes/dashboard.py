from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, Activity, Journey, ActivitySession
from app.utils.security import get_current_user
from app.utils.helpers import today_str, yesterday_str, greeting
from app.ai.recommendation_engine import recommend_daily_activities
from app.services.streak_service import compute_rank

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
async def dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = today_str()
    yesterday = yesterday_str()

    # Yesterday's stats
    y_result = await db.execute(
        select(Activity).where(Activity.user_id == user.id, Activity.date == yesterday)
    )
    y_acts = y_result.scalars().all()
    y_steps = sum(a.duration_minutes * 100 for a in y_acts)
    y_exercise = sum(a.duration_minutes for a in y_acts)
    y_calories = sum(a.calories_estimate for a in y_acts)
    y_completed = len([a for a in y_acts if a.status == "completed"])
    y_goal_pct = min(100, int((y_exercise / 45) * 100)) if y_exercise else 0

    # Today's stats
    t_result = await db.execute(
        select(Activity).where(Activity.user_id == user.id, Activity.date == today)
    )
    t_acts = t_result.scalars().all()
    t_exercise = sum(a.duration_minutes for a in t_acts)
    t_completed = len([a for a in t_acts if a.status == "completed"])
    t_goal_pct = min(100, int((t_exercise / 45) * 100)) if t_exercise else 0

    # Active session
    active_result = await db.execute(
        select(ActivitySession).where(
            ActivitySession.user_id == user.id,
            ActivitySession.status == "active"
        ).order_by(ActivitySession.start_time.desc()).limit(1)
    )
    active_session = active_result.scalar_one_or_none()

    # Recent activity types
    recent_result = await db.execute(
        select(Activity.activity_type).where(Activity.user_id == user.id).order_by(Activity.date.desc()).limit(10)
    )
    recent_types = [r[0] for r in recent_result.all()]

    profile = {
        "fitness_level": user.fitness_level,
        "activity_level": user.activity_level,
        "fitness_goal": user.fitness_goal,
    }
    recs = recommend_daily_activities(profile, recent_types)

    rank = await compute_rank(db, user.id)

    # Journey status
    ongoing_result = await db.execute(
        select(Journey).where(Journey.user_id == user.id, Journey.status == "ongoing")
    )
    ongoing_journey = ongoing_result.scalar_one_or_none()

    today_journey_result = await db.execute(
        select(Journey).where(Journey.user_id == user.id, Journey.date == today, Journey.status == "completed")
    )
    today_journey = today_journey_result.scalar_one_or_none()

    return {
        "greeting": greeting(), "name": user.name,
        "student_type": user.student_type or "day_scholar",
        "yesterday": {
            "steps": y_steps, "exercise_minutes": y_exercise,
            "calories": y_calories, "completed": y_completed, "goal_pct": y_goal_pct,
        },
        "today": {"exercise_minutes": t_exercise, "completed": t_completed, "goal_pct": t_goal_pct},
        "recommendations": recs,
        "streak": user.current_streak, "longest_streak": user.longest_streak,
        "points": user.points, "rank": rank,
        "active_session": {
            "id": active_session.id,
            "activity_type": active_session.activity_type,
            "start_time": str(active_session.start_time),
        } if active_session else None,
        "journey": {
            "ongoing": ongoing_journey.__dict__ if ongoing_journey else None,
            "today_completed": today_journey.__dict__ if today_journey else None,
        },
    }