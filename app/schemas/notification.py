
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum

class NotificationChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    INVALID = "invalid"

class NotificationBase(BaseModel):
    booking_id: UUID = Field(..., description="Booking UUID")
    type: str = Field(..., description="Type of notification")
    channel: NotificationChannel = Field(..., description="Notification channel")
    recipient: str = Field(..., description="Recipient (email or phone)")
    payload: Dict[str, Any] = Field(..., description="Notification payload data")
    scheduled_at: datetime = Field(..., description="Scheduled time for notification")
    max_attempts: int = Field(3, ge=1, le=10, description="Max retry attempts")

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    type: Optional[str] = Field(None, description="New notification type")
    channel: Optional[NotificationChannel] = Field(None, description="New notification channel")
    recipient: Optional[str] = Field(None, description="New recipient (email or phone)")
    payload: Optional[Dict[str, Any]] = Field(None, description="New notification payload data")
    scheduled_at: Optional[datetime] = Field(None, description="New scheduled time")
    status: Optional[NotificationStatus] = Field(None, description="New notification status")
    sent_at: Optional[datetime] = Field(None, description="Time notification was sent")
    attempts: Optional[int] = Field(None, ge=0, le=10, description="Current retry attempts")
    max_attempts: Optional[int] = Field(None, ge=1, le=10, description="New max retry attempts")

class NotificationRead(NotificationBase):
    id: UUID = Field(..., description="Notification UUID")
    status: NotificationStatus = Field(..., description="Status of the notification")
    sent_at: Optional[datetime] = Field(None, description="Time notification was sent")
    attempts: int = Field(..., description="Current retry attempts")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True
