from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class KourtType(str, Enum):
    TENNIS = "tennis"
    PADEL = "padel"
    PICKLEBALL = "pickleball"
    OTHER = "other"

class KourtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kourt name")
    type: KourtType = Field(..., description="Kourt type")
    capacity: int = Field(..., ge=1, le=20, description="Max player capacity")
    active: bool = Field(True, description="Is kourt active?")

class KourtCreate(KourtBase):
    pass

class KourtUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Kourt name")
    type: Optional[KourtType] = Field(None, description="Kourt type")
    capacity: Optional[int] = Field(None, ge=1, le=20, description="Max player capacity")
    active: Optional[bool] = Field(None, description="Is kourt active?")

class KourtRead(KourtBase):
    id: UUID = Field(..., description="Kourt UUID")
    venue_id: UUID = Field(..., description="Venue UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    class Config:
        from_attributes = True

class KourtListResponse(BaseModel):
    kourts: List[KourtRead]
    total: int

class KourtAvailabilityRequest(BaseModel):
    date: date = Field(..., description="Date for availability check")
    
class KourtAvailabilityResponse(BaseModel):
    available_intervals: List[dict] = Field(..., description="List of available time slots")
    total_available: int = Field(..., description="Total number of available slots")
    message: str = Field(..., description="Human-readable availability summary")