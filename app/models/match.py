from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID, uuid4


class Match(SQLModel, table=True):
    """
    Social match model for players to organize games together.
    
    Enables a social booking workflow where:
    1. A player creates a match for a specific time/date
    2. Other players can join the match until max_players is reached
    3. Optionally links to a booking once court reservation is made
    
    This allows social coordination before committing to court bookings,
    creating a more flexible and social booking experience.
    """
    __tablename__ = "matches"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    creator_id: UUID = Field(foreign_key="players.id")
    booking_id: Optional[UUID] = Field(default=None, foreign_key="bookings.id")
    date: date
    start_time: time
    end_time: time
    max_players: int
    num_players: int = 1
    status: str = Field(default="Open", sa_column_kwargs={"nullable": False})
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: Optional["Player"] = Relationship()
    booking: Optional["Booking"] = Relationship()
    players: List["MatchPlayer"] = Relationship(back_populates="match")
