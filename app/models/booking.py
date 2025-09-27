from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date, time
from typing import Optional
from uuid import UUID, uuid4
import secrets


class Booking(SQLModel, table=True):
    """
    Court booking model with anti-double-booking protection.
    
    Represents a reservation for a specific court at a venue for a time period.
    Includes secure cancellation tokens and prevents overlapping bookings through
    database-level constraints.
    """
    __tablename__ = "bookings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    venue_id: UUID = Field(foreign_key="venues.id")
    kourt_id: UUID = Field(foreign_key="kourts.id")
    date: date
    start_time: time      
    end_time: time        
    duration_minutes: int
    customer_name: str
    customer_phone: str
    cancellation_token: str = Field(default_factory=lambda: secrets.token_urlsafe(32), unique=True)
    status: str = Field(default="Booked", sa_column_kwargs={"nullable": False})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venue: Optional["Venue"] = Relationship(back_populates="bookings")
    kourt: Optional["Kourt"] = Relationship(back_populates="bookings")
