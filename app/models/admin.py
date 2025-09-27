from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

class Admin(SQLModel, table=True):
    """
    Admin user model for venue management.
    
    Admins can create and manage multiple venues, courts, and bookings.
    Each admin has a unique API key for authentication.
    """
    __tablename__ = "admins"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    api_key: str = Field(unique=True, index=True)
    name: str
    email: str  # For receiving booking confirmation notifications
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    venues: List["Venue"] = Relationship(back_populates="admin")
