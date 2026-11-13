from pydantic import BaseModel, Field
from typing import Optional


class JourneyStart(BaseModel):
    mode: str = Field(..., pattern="^(walking|cycling|bus|auto|own_vehicle)$")
    start_location: Optional[str] = None
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None


class JourneyStop(BaseModel):
    end_location: Optional[str] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    distance_km: Optional[float] = Field(None, ge=0, le=100)
