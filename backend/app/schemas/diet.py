from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class DietPersonalize(BaseModel):
    preferences: Optional[Dict[str, Any]] = None


class DietRecommendation(BaseModel):
    breakfast: List[str]
    lunch: List[str]
    dinner: List[str]
    snacks: List[str]
    hydration: str
    daily_calories_target: int
    notes: List[str]
