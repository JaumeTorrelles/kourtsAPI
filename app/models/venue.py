from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import json

class Venue(SQLModel, table=True):
    """
    Venue model representing sports facilities with flexible scheduling.
    
    Each venue belongs to an admin and contains multiple courts. Features:
    - Flexible opening hours stored as JSON (different schedules per day)
    - Configurable booking slot durations per venue
    - Multi-tenant architecture with admin ownership
    - Helper methods for JSON field manipulation with error handling
    
    Example opening_hours JSON:
    {
        "monday": {"open": "08:00", "close": "22:00"},
        "tuesday": {"open": "08:00", "close": "22:00"},
        "sunday": {"open": "09:00", "close": "18:00"}
    }
    """
    __tablename__ = "venues"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    admin_id: UUID = Field(foreign_key="admins.id")
    name: str
    address: str
    opening_hours: str = Field(default="{}")  # JSON string with schedules per day
    slot_duration_minutes: int = 30
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    admin: Optional["Admin"] = Relationship(back_populates="venues")
    kourts: List["Kourt"] = Relationship(back_populates="venue")
    bookings: List["Booking"] = Relationship(back_populates="venue")
    
    @property
    def opening_hours_dict(self) -> dict:
        """Returns opening_hours as a dictionary with error handling."""
        try:
            return json.loads(self.opening_hours)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_opening_hours(self, hours: dict):
        """Sets opening_hours from a dictionary by serializing to JSON."""
        self.opening_hours = json.dumps(hours)
