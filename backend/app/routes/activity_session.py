from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.database import get_db
from app.models import User, ActivitySession, Activity
from app.schemas.activity_session import SessionStart, SessionStop, SessionResponse
from app.utils.security import get_current_user
from app.utils.helpers import today_str, estimate_calories
from app.services.streak_service import update_streak

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _to_response(s: ActivitySession) -> dict:
    return {
        "id": s.id, "activity_type": s.activity_type,
        "start_time": str(s.start_time),
        "end_time": str(s.end_time) if s.end_time else None,
        "duration_seconds": s.duration_seconds or 0,
        "steps_count": s.steps_count or 0,
        "distance_km": s.distance_km or 0,
        "calories_estimate": s.calories_estimate or 0,
        "status": s.status,
    }


@router.get("/active")
async def get_active_session(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current active session (if any)."""
    result = await db.execute(
        select(ActivitySession).where(
            ActivitySession.user_id == user.id,
            ActivitySession.status == "active"
        ).order_by(ActivitySession.start_time.desc()).limit(1)
    )
    session = result.scalar_one_or_none()
    return {"active": _to_response(session) if session else None}


@router.post("/start", response_model=SessionResponse)
async def start_session(req: SessionStart, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Start a new activity session. Cancels any existing active session."""
    # Cancel existing active session
    await db.execute(
        update(ActivitySession)
        .where(ActivitySession.user_id == user.id, ActivitySession.status == "active")
        .values(status="cancelled")
    )

    session = ActivitySession(
        user_id=user.id,
        activity_type=req.activity_type,
        start_time=datetime.utcnow(),
        status="active",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _to_response(session)


@router.post("/{session_id}/stop", response_model=SessionResponse)
async def stop_session(
    session_id: int, req: SessionStop,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop an active session and save metrics."""
    result = await db.execute(
        select(ActivitySession).where(
            ActivitySession.id == session_id,
            ActivitySession.user_id == user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")
    if session.status != "active":
        raise HTTPException(400, "Session is not active")

    end_time = datetime.utcnow()
    duration_seconds = int((end_time - session.start_time).total_seconds())
    duration_minutes = max(1, duration_seconds // 60)

    # Estimate calories based on activity type and duration
    calories = estimate_calories(session.activity_type, duration_minutes)

    # Update session
    session.end_time = end_time
    session.duration_seconds = duration_seconds
    session.steps_count = req.steps_count or 0
    session.distance_km = req.distance_km or 0
    session.calories_estimate = calories
    session.notes = req.notes
    session.status = "completed"

    # Points
    pts = max(5, duration_minutes // 2)

    # Also log as an Activity record for history
    activity = Activity(
        user_id=user.id,
        activity_type=session.activity_type,
        duration_minutes=duration_minutes,
        calories_estimate=calories,
        status="completed",
        date=today_str(),
        points_earned=pts,
        source="session",
        created_at=datetime.utcnow(),
    )
    db.add(activity)

    # Update user points and streak
    await db.execute(update(User).where(User.id == user.id).values(points=User.points + pts))
    await db.commit()
    await update_streak(db, user.id, today_str())
    await db.refresh(session)

    return {**_to_response(session), "points_earned": pts}


@router.get("/history")
async def session_history(
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActivitySession)
        .where(ActivitySession.user_id == user.id)
        .order_by(ActivitySession.start_time.desc())
        .limit(limit)
    )
    return [_to_response(s) for s in result.scalars().all()]


@router.get("/today")
async def today_sessions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    today = today_str()
    result = await db.execute(
        select(ActivitySession)
        .where(ActivitySession.user_id == user.id)
        .order_by(ActivitySession.start_time.desc())
    )
    sessions = result.scalars().all()
    # Filter to today's sessions
    today_sessions = [s for s in sessions if s.start_time.strftime("%Y-%m-%d") == today]
    return [_to_response(s) for s in today_sessions]