from pydantic import BaseModel, Field
from typing import Optional, List


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    student_type: Optional[str] = Field(None, pattern="^(hosteler|day_scholar)$")
    age: Optional[int] = Field(None, ge=10, le=100)
    weight: Optional[float] = Field(None, ge=20, le=300)
    height: Optional[float] = Field(None, ge=100, le=250)
    body_type: Optional[str] = Field(None, pattern="^(slim|average|athletic|curvy|broad)$")
    fitness_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    activity_level: Optional[str] = Field(None, pattern="^(low|moderate|high|very_high)$")
    fitness_goal: Optional[str] = Field(None, pattern="^(stay_active|improve_fitness|build_strength|improve_endurance|general_wellness)$")
    dietary_preference: Optional[str] = Field(None, pattern="^(veg|non_veg|vegan|eggetarian)$")
    allergies: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    student_type: str
    age: Optional[int] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    body_type: Optional[str] = None
    fitness_level: Optional[str] = None
    activity_level: Optional[str] = None
    fitness_goal: Optional[str] = None
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = []
    points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    last_activity_date: Optional[str] = None
    rank: Optional[int] = None