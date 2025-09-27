from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID
from typing import Optional

class MatchPlayer(SQLModel, table=True):
    """
    Junction table managing many-to-many relationships between matches and players.
    
    Tracks which players have joined which matches, with timestamp tracking
    for when each player joined. Uses composite primary key to ensure
    each player can only join a match once.
    """
    __tablename__ = "match_players"

    match_id: UUID = Field(foreign_key="matches.id", primary_key=True)
    player_id: UUID = Field(foreign_key="players.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    match: Optional["Match"] = Relationship(back_populates="players")
    player: Optional["Player"] = Relationship()
