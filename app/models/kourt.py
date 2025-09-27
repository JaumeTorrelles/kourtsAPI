from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

class Kourt(SQLModel, table=True):
    """
    Sports court model representing individual courts within a venue.
    
    Each court belongs to a venue and can be booked by customers.
    Supports multiple sports types (tennis, padel, futsal, etc.) and
    includes capacity management and soft deletion via the active flag.
    """
    __tablename__ = "kourts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    venue_id: UUID = Field(foreign_key="venues.id")
    name: str
    type: str  # Sport type: tennis, padel, futsal, basketball, etc.
    capacity: int
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venue: Optional["Venue"] = Relationship(back_populates="kourts")
    bookings: List["Booking"] = Relationship(back_populates="kourt")
