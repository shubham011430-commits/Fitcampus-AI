from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import math

from app.database import get_db
from app.models import User, Journey, Activity
from app.schemas.journey import JourneyStart, JourneyStop
from app.utils.security import get_current_user
from app.services.streak_service import update_streak
from app.utils.helpers import today_str
from app.ai.canteen_recommender import recommend_canteen_meal

router = APIRouter(prefix="/api/journey", tags=["journey"])

MIN_JOURNEY_MINUTES_FOR_POINTS = 2  # anti points-farming


def _haversine(lat1, lon1, lat2, lon2) -> float:
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_calories(mode: str, duration_min: int, distance_km: float) -> int:
    met = {"walking": 3.8, "cycling": 6.0, "bus": 1.3, "auto": 1.0, "own_vehicle": 1.2}.get(mode, 2.0)
    base = met * 70 * (duration_min / 60.0)
    if mode in ("walking", "cycling") and distance_km > 0:
        base += distance_km * 30
    return int(base)


def _estimate_steps(mode: str, duration_min: int, distance_km: float) -> int:
    if mode == "walking":
        return int(distance_km * 1300) if distance_km > 0 else int(duration_min * 100)
    if mode == "cycling":
        return int(duration_min * 20)
    return 0


def _journey_to_dict(j: Journey) -> dict:
    # Stored as naive UTC -> append "Z" so browsers parse the timezone correctly
    return {
        "id": j.id, "mode": j.mode,
        "start_time": j.start_time.isoformat() + "Z",
        "end_time": (j.end_time.isoformat() + "Z") if j.end_time else None,
        "duration_minutes": j.duration_minutes or 0, "distance_km": j.distance_km or 0,
        "calories_burned": j.calories_burned or 0, "steps_estimate": j.steps_estimate or 0,
        "status": j.status, "points_earned": j.points_earned or 0,
    }


async def _latest(db: AsyncSession, user_id: int, *conditions, order=None):
    q = select(Journey).where(Journey.user_id == user_id, *conditions).order_by(order or Journey.start_time.desc()).limit(1)
    return (await db.execute(q)).scalars().first()


@router.get("/status")
async def journey_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ongoing = await _latest(db, user.id, Journey.status == "ongoing")
    return {"ongoing": _journey_to_dict(ongoing) if ongoing else None}


@router.post("/start")
async def start_journey(req: JourneyStart, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(Journey).where(Journey.user_id == user.id, Journey.status == "ongoing")
                     .values(status="cancelled"))
    j = Journey(
        user_id=user.id, mode=req.mode, start_time=datetime.utcnow(),
        start_location=req.start_location, start_lat=req.start_lat, start_lng=req.start_lng,
        status="ongoing", date=today_str(),
    )
    db.add(j)
    await db.commit()
    await db.refresh(j)
    return _journey_to_dict(j)


@router.post("/{journey_id}/stop")
async def stop_journey(journey_id: int, req: JourneyStop, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Journey).where(Journey.id == journey_id, Journey.user_id == user.id))
    journey = result.scalar_one_or_none()
    if not journey:
        raise HTTPException(404, "Journey not found")
    if journey.status != "ongoing":
        raise HTTPException(400, "Journey already completed")

    distance = req.distance_km or _haversine(journey.start_lat, journey.start_lng, req.end_lat, req.end_lng)
    end_dt = datetime.utcnow()
    duration_min = max(1, int((end_dt - journey.start_time).total_seconds() / 60))

    calories = _estimate_calories(journey.mode, duration_min, distance)
    steps = _estimate_steps(journey.mode, duration_min, distance)

    if duration_min < MIN_JOURNEY_MINUTES_FOR_POINTS:
        pts = 0
    else:
        pts = duration_min // 3
        if journey.mode in ("walking", "cycling"):
            pts += int(distance * 5)
        pts = max(5, pts)

    await db.execute(update(Journey).where(Journey.id == journey_id).values(
        end_time=end_dt, end_location=req.end_location,
        end_lat=req.end_lat, end_lng=req.end_lng,
        distance_km=round(distance, 2), duration_minutes=duration_min,
        calories_burned=calories, steps_estimate=steps,
        status="completed", points_earned=pts,
    ))
    if pts:
        await db.execute(update(User).where(User.id == user.id).values(points=User.points + pts))
    db.add(Activity(
        user_id=user.id,
        activity_type=journey.mode if journey.mode in ("walking", "cycling") else "general",
        duration_minutes=duration_min, calories_estimate=calories,
        status="completed", date=today_str(), points_earned=pts,
        source="journey", created_at=datetime.utcnow(),
    ))
    await db.commit()
    if pts:
        await update_streak(db, user.id, today_str())

    await db.refresh(journey)
    msg = f"Journey completed! +{pts} points 🎉" if pts else "Journey completed (too short to earn points)"
    return {"ok": True, "journey": _journey_to_dict(journey), "points_earned": pts, "message": msg}


@router.post("/{journey_id}/cancel")
async def cancel_journey(journey_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        update(Journey)
        .where(Journey.id == journey_id, Journey.user_id == user.id, Journey.status == "ongoing")
        .values(status="cancelled")
    )
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(404, "No ongoing journey found")
    return {"ok": True}


@router.get("/history")
async def journey_history(limit: int = 10, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    limit = max(1, min(limit, 100))
    result = await db.execute(
        select(Journey).where(Journey.user_id == user.id).order_by(Journey.start_time.desc()).limit(limit)
    )
    return [_journey_to_dict(j) for j in result.scalars().all()]


@router.get("/canteen-recommendation")
async def canteen_recommendation(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    journey = await _latest(db, user.id, Journey.date == today_str(), Journey.status == "completed",
                            order=Journey.end_time.desc())
    profile = {"fitness_goal": user.fitness_goal, "fitness_level": user.fitness_level, "weight": user.weight}
    return recommend_canteen_meal(profile, _journey_to_dict(journey) if journey else None)
