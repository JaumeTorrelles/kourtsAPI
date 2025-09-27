from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlmodel import SQLModel, Field


class Player(SQLModel, table=True):
    """
    Player model supporting flexible authentication and matchmaking.
    
    Designed for phone-first user experience with support for:
    - Anonymous players (just name + phone for quick bookings)
    - Social auth providers (Google, WhatsApp, etc.)
    - Skill level system for intelligent match-making
    - Progressive user onboarding from anonymous to authenticated
    """
    __tablename__ = "players"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(..., nullable=False)
    phone: str = Field(..., nullable=False)
    email: Optional[str] = None
    level: float = Field(default=1.0)
    auth_provider: Optional[str] = Field(
        default=None, description="e.g., 'google', 'whatsapp', NULL = anonymous user"
    )
    auth_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
