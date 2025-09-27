from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import datetime

class BookingVenueBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Venue name")

class BookingVenueCreate(BookingVenueBase):
    pass

class BookingVenueRead(BookingVenueBase):
    id: UUID = Field(..., description="Venue UUID")
    class Config:
        from_attributes = True

class BookingKourtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Kourt name")

class BookingKourtCreate(BookingKourtBase):
    pass

class BookingKourtRead(BookingKourtBase):
    id: UUID = Field(..., description="Kourt UUID")
    class Config:
        from_attributes = True

class BookingBase(BaseModel):
    date: datetime.date = Field(..., description="Booking date")
    start_time: datetime.time = Field(..., description="Start time")
    end_time: datetime.time = Field(..., description="End time")
    duration_minutes: int = Field(..., ge=1, le=480, description="Duration in minutes")
    customer_name: str = Field(..., min_length=1, max_length=100, description="Customer name")
    customer_phone: str = Field(..., min_length=6, max_length=20, description="Customer phone")
    status: str = Field(..., description="Booking status")
    venue_id: UUID = Field(..., description="Venue UUID")
    kourt_id: UUID = Field(..., description="Kourt UUID")

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    date: Optional[datetime.date] = Field(None, description="New booking date")
    start_time: Optional[datetime.time] = Field(None, description="New start time")
    end_time: Optional[datetime.time] = Field(None, description="New end time")
    duration_minutes: Optional[int] = Field(None, ge=1, le=480, description="New duration in minutes")
    customer_name: Optional[str] = Field(None, min_length=1, max_length=100, description="New customer name")
    customer_phone: Optional[str] = Field(None, min_length=6, max_length=20, description="New customer phone")
    status: Optional[str] = Field(None, description="New booking status")
    venue_id: Optional[UUID] = Field(None, description="New venue UUID")
    kourt_id: Optional[UUID] = Field(None, description="New kourt UUID")

class BookingRead(BookingBase):
    id: UUID = Field(..., description="Booking UUID")
    venue: Optional[BookingVenueRead] = None
    kourt: Optional[BookingKourtRead] = None
    created_at: datetime.datetime = Field(..., description="Creation timestamp")
    class Config:
        from_attributes = True

class BookingListResponse(BaseModel):
    bookings: List[BookingRead]
    total: int

class BookingFilter(BaseModel):
    date_filter: Optional[datetime.date] = Field(None, description="Filter by booking date")
    status: Optional[str] = Field(None, description="Filter by booking status")
    customer_name: Optional[str] = Field(None, description="Filter by customer name")
    skip: int = Field(0, ge=0, description="Number of records to skip (pagination)")
    limit: int = Field(100, ge=1, le=500, description="Maximum number of records to return")