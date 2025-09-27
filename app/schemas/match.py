from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
import datetime
from enum import Enum

class MatchStatus(str, Enum):
    OPEN = "open"
    FULL = "full"
    BOOKED = "booked"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class MatchPlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Player name")
    level: float = Field(..., ge=0, le=10, description="Player level")

class MatchPlayerCreate(MatchPlayerBase):
    pass

class MatchPlayerRead(MatchPlayerBase):
    id: UUID = Field(..., description="Player UUID")
    class Config:
        from_attributes = True

class MatchBase(BaseModel):
    date: datetime.date = Field(..., description="Match date")
    start_time: datetime.time = Field(..., description="Start time")
    end_time: datetime.time = Field(..., description="End time")
    max_players: int = Field(..., ge=2, le=20, description="Max players")
    status: MatchStatus = Field(..., description="Match status")

class MatchCreate(MatchBase):
    creator_name: str = Field(..., min_length=1, max_length=100, description="Creator name")
    creator_phone: str = Field(..., min_length=6, max_length=20, description="Creator phone")

class MatchUpdate(BaseModel):
    date: Optional[datetime.date] = Field(None, description="New match date")
    start_time: Optional[datetime.time] = Field(None, description="New start time")
    end_time: Optional[datetime.time] = Field(None, description="New end time")
    max_players: Optional[int] = Field(None, ge=2, le=20, description="New max players")
    status: Optional[MatchStatus] = Field(None, description="New match status")

class MatchRead(MatchBase):
    id: UUID = Field(..., description="Match UUID")
    num_players: int = Field(..., ge=0, description="Current number of players")
    players: List[MatchPlayerRead] = Field(default_factory=list, description="Players in match")
    created_at: datetime.datetime = Field(..., description="Creation timestamp")
    class Config:
        from_attributes = True

class MatchListResponse(BaseModel):
    matches: List[MatchRead] = Field(..., description="List of matches")
    total: int = Field(..., description="Total number of matches")

class MatchActionResponse(BaseModel):
    message: str = Field(..., description="Action result message")
    match_id: Optional[UUID] = Field(None, description="Match UUID if applicable")