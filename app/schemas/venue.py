
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import json

class VenueBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Venue name")
    address: str = Field(..., min_length=1, max_length=200, description="Venue address")
    opening_hours: Dict[str, Any] = Field(default_factory=dict, description="Opening hours per day (JSON)")
    slot_duration_minutes: int = Field(default=30, ge=15, le=120, description="Slot duration in minutes")

    @field_validator('opening_hours', mode='before')
    @classmethod
    def validate_opening_hours(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('opening_hours must be valid JSON')
        return v

class VenueCreate(VenueBase):
    pass

class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Venue name")
    address: Optional[str] = Field(None, min_length=1, max_length=200, description="Venue address")
    opening_hours: Optional[Dict[str, Any]] = Field(None, description="Opening hours per day (JSON)")
    slot_duration_minutes: Optional[int] = Field(None, ge=15, le=120, description="Slot duration in minutes")

    @field_validator('opening_hours', mode='before')
    @classmethod
    def validate_opening_hours(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                raise ValueError('opening_hours must be valid JSON')
        return v

class VenueRead(VenueBase):
    id: UUID = Field(..., description="Venue UUID")
    admin_id: UUID = Field(..., description="Admin UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    class Config:
        from_attributes = True

class VenueListResponse(BaseModel):
    venues: List[VenueRead] = Field(..., description="List of venues")
    total: int = Field(..., description="Total number of venues")
