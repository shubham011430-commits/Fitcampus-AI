from pydantic import BaseModel, Field
from typing import List, Dict


class ExerciseComplete(BaseModel):
    exercise_name: str = Field(..., max_length=100)
    repetitions: int = Field(..., ge=0, le=300)
    duration_seconds: int = Field(..., ge=0, le=3600)
    form_score: float = Field(..., ge=0, le=100)

class FormAnalysisRequest(BaseModel):
    exercise: str = Field(..., pattern="^(squat|pushup)$")
    landmarks: List[Dict[str, float]] = []
    angles: Dict[str, float] = {}
    phase: str
    rep_count: int
    form_score: float


class FormAnalysisResponse(BaseModel):
    feedback: str
    form_score: float
    rep_count: int
    phase: str
    saved: bool
