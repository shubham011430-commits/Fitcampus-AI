from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def user_to_dict(u: User) -> dict:
    return {
        "id": u.id, "name": u.name, "email": u.email,
        "student_type": u.student_type,
        "age": u.age, "weight": u.weight, "height": u.height,
        "body_type": u.body_type, "fitness_level": u.fitness_level,
        "activity_level": u.activity_level, "fitness_goal": u.fitness_goal,
        "dietary_preference": u.dietary_preference,
        "allergies": u.allergies or [],
        "points": u.points, "current_streak": u.current_streak,
        "longest_streak": u.longest_streak, "last_activity_date": u.last_activity_date,
    }


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=req.name, email=req.email, password_hash=hash_password(req.password),
        student_type=req.student_type,
        age=req.age, weight=req.weight, height=req.height,
        fitness_level="beginner", activity_level="low", fitness_goal="general_wellness",
        dietary_preference="veg", allergies=[],
        points=0, current_streak=0, longest_streak=0,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token({"sub": user.id, "email": user.email}) 
    return TokenResponse(access_token=token, user=user_to_dict(user))


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(access_token=token, user=user_to_dict(user))