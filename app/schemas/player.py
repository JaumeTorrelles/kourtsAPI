
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from enum import Enum

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"

class PlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Player name")
    phone: str = Field(..., min_length=6, max_length=20, description="Player phone")
    email: Optional[EmailStr] = Field(None, description="Player email")
    level: float = Field(1.0, ge=1, le=7, description="Player level")
    auth_provider: Optional[AuthProvider] = Field(None, description="Auth provider")
    auth_id: Optional[str] = Field(None, description="Provider user id")

class PlayerCreate(PlayerBase):
    pass

class PlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Player name")
    phone: Optional[str] = Field(None, min_length=6, max_length=20, description="Player phone")
    email: Optional[EmailStr] = Field(None, description="Player email")
    level: Optional[float] = Field(None, ge=1, le=7, description="Player level")
    auth_provider: Optional[AuthProvider] = Field(None, description="Auth provider")
    auth_id: Optional[str] = Field(None, description="Provider user id")

class PlayerRead(PlayerBase):
    id: UUID = Field(..., description="Player UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    class Config:
        from_attributes = True

class PlayerListResponse(BaseModel):
    players: List[PlayerRead] = Field(..., description="List of players")
    total: int = Field(..., description="Total number of players")

class JoinMatchRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=100, description="Player name")
    player_phone: str = Field(..., min_length=6, max_length=20, description="Player phone")

class LeaveMatchRequest(BaseModel):
    player_phone: str = Field(..., min_length=6, max_length=20, description="Player phone")