from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, FormSnapshot
from app.schemas.exercise import FormAnalysisRequest, FormAnalysisResponse
from app.utils.security import get_current_user
from app.ai.form_analyzer import analyze

router = APIRouter(prefix="/api/form", tags=["form"])

EXERCISES_INFO = [
    {"name": "squat", "label": "Squat", "description": "Feet shoulder-width, chest up, lower until thighs parallel."},
    {"name": "pushup", "label": "Push-up", "description": "Hands shoulder-width, body straight, lower until elbows ~90°."},
]


@router.get("/exercises")
async def form_exercises():
    return EXERCISES_INFO


@router.post("/analyze", response_model=FormAnalysisResponse)
async def analyze_form(req: FormAnalysisRequest, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    result = analyze({"exercise": req.exercise, "angles": req.angles,
                      "phase": req.phase, "rep_count": req.rep_count})
    db.add(FormSnapshot(
        user_id=user.id, exercise=req.exercise, angles=req.angles,
        phase=req.phase, rep_count=req.rep_count,
        form_score=result["form_score"], feedback=result["feedback"],
        created_at=datetime.utcnow(),
    ))
    await db.commit()
    return FormAnalysisResponse(
        feedback=result["feedback"], form_score=result["form_score"],
        rep_count=result["rep_count"], phase=result["phase"], saved=True,
    )
