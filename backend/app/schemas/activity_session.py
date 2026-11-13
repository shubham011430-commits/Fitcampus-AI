from pydantic import BaseModel, Field
from typing import Optional


class SessionStart(BaseModel):
    activity_type: str = Field(..., pattern="^(walking|running|cycling|yoga|sports|general)$")


class SessionStop(BaseModel):
    steps_count: Optional[int] = Field(None, ge=0)
    distance_km: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    activity_type: str
    start_time: str
    end_time: Optional[str]
    duration_seconds: int
    steps_count: int
    distance_km: float
    calories_estimate: int
    status: str