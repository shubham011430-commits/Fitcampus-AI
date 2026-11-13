from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    email: EmailStr
    password: str = Field(..., min_length=6)
    student_type: str = Field(..., pattern="^(hosteler|day_scholar)$")
    age: Optional[int] = Field(None, ge=10, le=100)
    weight: Optional[float] = Field(None, ge=20, le=300)
    height: Optional[float] = Field(None, ge=100, le=250)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict