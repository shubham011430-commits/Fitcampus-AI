from pydantic import BaseModel, Field
from typing import Optional, List


class MenuItemCreate(BaseModel):
    menu_type: str = Field(..., pattern="^(hostel_mess|college_canteen)$")
    meal_type: str = Field(..., pattern="^(breakfast|lunch|snacks|dinner)$")
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field("veg", pattern="^(veg|non_veg|vegan|beverages|snacks)$")
    description: Optional[str] = None
    calories: Optional[int] = Field(None, ge=0, le=2000)
    protein_g: Optional[float] = Field(None, ge=0)
    carbs_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    price: Optional[float] = Field(None, ge=0)
    timing: Optional[str] = None
    allergens: Optional[List[str]] = []


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    price: Optional[float] = None
    timing: Optional[str] = None
    allergens: Optional[List[str]] = None
    available: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: int
    menu_type: str
    meal_type: str
    name: str
    category: str
    description: Optional[str]
    calories: Optional[int]
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    price: Optional[float]
    timing: Optional[str]
    allergens: List[str]
    available: bool