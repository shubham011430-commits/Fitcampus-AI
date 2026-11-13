from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.database import get_db
from app.models import User, MenuItem, DietRecommendation as DietRecModel
from app.schemas.diet import DietRecommendation, DietPersonalize
from app.utils.security import get_current_user
from app.ai.diet_recommender import recommend_diet

router = APIRouter(prefix="/api/diet", tags=["diet"])


@router.get("/recommendation", response_model=DietRecommendation)
async def diet_recommendation(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Get menu items for this student's type
    menu_type = "hostel_mess" if user.student_type == "hosteler" else "college_canteen"
    result = await db.execute(
        select(MenuItem).where(MenuItem.menu_type == menu_type, MenuItem.available == True)
    )
    menu_items = [
        {
            "name": i.name, "meal_type": i.meal_type, "category": i.category,
            "calories": i.calories, "allergens": i.allergens or [],
        }
        for i in result.scalars().all()
    ]

    profile = {
        "name": user.name, "age": user.age, "weight": user.weight, "height": user.height,
        "fitness_level": user.fitness_level, "activity_level": user.activity_level,
        "fitness_goal": user.fitness_goal, "dietary_preference": user.dietary_preference,
        "allergies": user.allergies or [], "student_type": user.student_type,
    }

    rec = await recommend_diet(profile, menu_items)
    source = rec.get("source", "rule_based")

    # Save to DB
    db.add(DietRecModel(
        user_id=user.id,
        profile_snapshot=profile,
        recommendations=rec,
        source=source,
        generated_at=datetime.utcnow(),
    ))
    await db.commit()

    return DietRecommendation(
        breakfast=rec.get("breakfast", []),
        lunch=rec.get("lunch", []),
        dinner=rec.get("dinner", []),
        snacks=rec.get("snacks", []),
        hydration=rec.get("hydration", "2-3 L water daily"),
        daily_calories_target=rec.get("daily_calories_target", 2000),
        notes=rec.get("tips", []) + [rec.get("reasoning", "")],
    )


@router.post("/personalize", response_model=DietRecommendation)
async def personalize_diet(req: DietPersonalize, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    prefs = req.preferences or {}
    updates = {}
    if prefs.get("fitness_goal"): updates["fitness_goal"] = prefs["fitness_goal"]
    if prefs.get("dietary_preference"): updates["dietary_preference"] = prefs["dietary_preference"]
    if prefs.get("allergies") is not None: updates["allergies"] = prefs["allergies"]
    if updates:
        await db.execute(update(User).where(User.id == user.id).values(**updates))
        await db.commit()
        await db.refresh(user)
    return await diet_recommendation(user, db)