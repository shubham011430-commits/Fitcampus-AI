from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models import User, ChatHistory
from app.schemas.assistant import ChatRequest, ChatResponse
from app.utils.security import get_current_user
from app.ai import fitness_assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db.add(ChatHistory(user_id=user.id, role="user", message=req.message, created_at=datetime.utcnow()))
    profile = {
        "name": user.name, "fitness_level": user.fitness_level,
        "activity_level": user.activity_level, "fitness_goal": user.fitness_goal,
        "points": user.points, "current_streak": user.current_streak,
    }
    result = await fitness_assistant.chat(req.message, profile)
    db.add(ChatHistory(user_id=user.id, role="assistant", message=result["reply"],
                       source=result["source"], created_at=datetime.utcnow()))
    await db.commit()
    return ChatResponse(reply=result["reply"], source=result["source"])


@router.get("/history")
async def history(limit: int = 50, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(ChatHistory).where(ChatHistory.user_id == user.id)
        .order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc()).limit(limit)
    )
    msgs = list(result.scalars().all())
    msgs.reverse()
    return [{"role": m.role, "message": m.message, "created_at": str(m.created_at)} for m in msgs]
