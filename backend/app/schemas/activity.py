from pydantic import BaseModel, Field
from typing import Optional


class ActivityCreate(BaseModel):
    activity_type: str = Field(..., pattern="^(walking|running|stretching|sports|yoga|general)$")
    duration_minutes: int = Field(..., ge=1, le=600)
    calories_estimate: Optional[int] = Field(None, ge=0)


class ActivityResponse(BaseModel):
    id: int
    activity_type: str
    duration_minutes: int
    calories_estimate: int
    status: str
    date: str
    points_earned: int
