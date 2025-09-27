from sqlmodel import SQLModel, Field, Column
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class NotificationQueue(SQLModel, table=True):
    """
    Database-backed notification queue for reliable message delivery.
    
    Implements a robust background job processing system with:
    - PostgreSQL JSONB storage for flexible message payloads
    - Automatic retry logic with configurable max attempts
    - Multi-channel support (email, WhatsApp, SMS, etc.)
    - Complete audit trail with scheduling and delivery timestamps
    - Status tracking for monitoring and debugging
    
    Supports notification types like booking confirmations, reminders,
    cancellations, and promotional messages. The queue ensures reliable
    delivery even if external services are temporarily unavailable.
    """
    __tablename__ = "notification_queue"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    booking_id: UUID = Field(foreign_key="bookings.id")
    type: str
    channel: str
    recipient: str
    payload: dict = Field(sa_column=Column(JSONB))
    status: str = Field(default="pending")
    scheduled_at: datetime
    sent_at: Optional[datetime] = None
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
