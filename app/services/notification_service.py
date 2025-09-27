from typing import List, Optional
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select
from app.models.notification import NotificationQueue
from app.schemas.notification import NotificationCreate, NotificationRead, NotificationStatus, NotificationChannel
from app.core.database import get_session

class NotificationService:
    """
    Enterprise-grade notification service handling multi-channel background jobs.
    Supports email and WhatsApp with advanced retry logic and batch processing.
    
    Architecture Note:
        This service uses synchronous database operations (not async) because it's designed
        for background worker consumption rather than API endpoints. Workers typically use
        sync operations for better reliability and simpler error handling.
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or get_session()

    def create_notification(self, notification_data: NotificationCreate) -> NotificationRead:
        """
        Creates a new notification in the background job queue.
        Supports email and WhatsApp channels with scheduled delivery.
        
        Args:
            notification_data: Notification creation data including type, channel, recipient, payload
            
        Returns:
            NotificationRead: The newly created notification with queue details
            
        Note:
            Notifications are stored with PENDING status for worker processing
        """
        notification = NotificationQueue(
            booking_id=notification_data.booking_id,
            type=notification_data.type,
            channel=notification_data.channel.value if isinstance(notification_data.channel, NotificationChannel) else notification_data.channel,
            recipient=notification_data.recipient,
            payload=notification_data.payload,
            scheduled_at=notification_data.scheduled_at,
            status=NotificationStatus.PENDING.value,
            max_attempts=notification_data.max_attempts
        )
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return NotificationRead.model_validate(notification)

    def list_notifications(
        self,
        booking_id: Optional[UUID] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
        scheduled_from: Optional[datetime] = None,
        scheduled_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[NotificationRead]:
        """
        Lists notifications with advanced filtering and pagination.
        Efficiently builds dynamic queries to avoid unnecessary database load.
        
        Args:
            booking_id: Filter by specific booking ID
            status: Filter by notification status (PENDING, SENT, FAILED, etc.)
            channel: Filter by communication channel (email, whatsapp)
            scheduled_from: Filter notifications scheduled from this datetime
            scheduled_to: Filter notifications scheduled until this datetime
            limit: Maximum number of results to return (default: 100)
            offset: Number of results to skip for pagination (default: 0)
            
        Returns:
            List[NotificationRead]: Filtered list of notifications
        """
        query = select(NotificationQueue)
        if booking_id is not None:
            query = query.where(NotificationQueue.booking_id == booking_id)
        if status is not None:
            query = query.where(NotificationQueue.status == status)
        if channel is not None:
            query = query.where(NotificationQueue.channel == channel)
        if scheduled_from is not None:
            query = query.where(NotificationQueue.scheduled_at >= scheduled_from)
        if scheduled_to is not None:
            query = query.where(NotificationQueue.scheduled_at <= scheduled_to)
        query = query.offset(offset).limit(limit)
        results = self.session.exec(query).all()
        return [NotificationRead.model_validate(n) for n in results]

    def get_notification_by_id(self, notification_id: int) -> Optional[NotificationRead]:
        """
        Retrieves notification details by ID using efficient primary key lookup.
        
        Args:
            notification_id: Primary key of the notification
            
        Returns:
            Optional[NotificationRead]: Notification details or None if not found
        """
        notification = self.session.get(NotificationQueue, notification_id)
        return NotificationRead.model_validate(notification) if notification else None

    def update_notification_status(
        self,
        notification_id: int,
        new_status: str,
        sent_at: Optional[datetime] = None
    ) -> Optional[NotificationRead]:
        """
        Updates notification status and optionally marks delivery timestamp.
        Used by workers to track notification processing lifecycle.
        
        Args:
            notification_id: ID of the notification to update
            new_status: New status (PENDING, SENT, FAILED, etc.)
            sent_at: Optional timestamp when notification was delivered
            
        Returns:
            Optional[NotificationRead]: Updated notification or None if not found
        """
        notification = self.get_notification_by_id(notification_id)
        if not notification:
            return None
        db_notification = self.session.get(NotificationQueue, notification_id)
        db_notification.status = new_status
        if sent_at is not None:
            db_notification.sent_at = sent_at
        self.session.add(db_notification)
        self.session.commit()
        self.session.refresh(db_notification)
        return NotificationRead.model_validate(db_notification)

    def delete_notification(self, notification_id: int) -> bool:
        """
        Safely removes a notification from the queue.
        Typically used for cleaning up old processed notifications.
        
        Args:
            notification_id: ID of the notification to delete
            
        Returns:
            bool: True if deletion was successful, False if notification not found
        """
        notification = self.get_notification_by_id(notification_id)
        if not notification:
            return False
        # Get the actual database object for deletion
        db_notification = self.session.get(NotificationQueue, notification_id)
        self.session.delete(db_notification)
        self.session.commit()
        return True

    def retry_failed_notification(self, notification_id: int) -> Optional[NotificationRead]:
        """
        Retries a failed notification by resetting status and incrementing attempt counter.
        Implements smart retry logic with attempt tracking for reliable delivery.
        
        Args:
            notification_id: ID of the failed notification to retry
            
        Returns:
            Optional[NotificationRead]: Retried notification or None if not eligible
            
        Note:
            Only FAILED notifications can be retried, and they're rescheduled for immediate processing
        """
        db_notification = self.session.get(NotificationQueue, notification_id)
        if not db_notification or db_notification.status != NotificationStatus.FAILED.value:
            return None
        db_notification.status = NotificationStatus.PENDING.value
        db_notification.scheduled_at = datetime.utcnow()
        db_notification.attempts = (db_notification.attempts or 0) + 1
        self.session.add(db_notification)
        self.session.commit()
        self.session.refresh(db_notification)
        return NotificationRead.model_validate(db_notification)

    def get_pending_notifications(self, max_batch: int = 20) -> List[NotificationRead]:
        """
        Retrieves pending notifications for background worker processing.
        Optimized query prevents N+1 issues and controls worker batch size.
        
        Only processes notifications with:
        - Status: PENDING
        - Attempts < max_attempts (prevents infinite retries)
        - Scheduled time <= now (respects scheduling)
        
        Args:
            max_batch: Maximum number of notifications to return (default: 20)
            
        Returns:
            List[NotificationRead]: Batch of notifications ready for processing
            
        Note:
            Used by background workers to fetch workload in controlled batches
        """
        now = datetime.utcnow()
        query = select(NotificationQueue).where(
            NotificationQueue.status == NotificationStatus.PENDING.value,
            NotificationQueue.attempts < NotificationQueue.max_attempts,
            NotificationQueue.scheduled_at <= now
        ).limit(max_batch)
        notifications = self.session.exec(query).all()
        # Integration point for sending logic (email, WhatsApp providers) and status updates
        return [NotificationRead.model_validate(n) for n in notifications]
    
    def validate_notification(self, notification: NotificationQueue) -> bool:
        """
        Validates notification channel and payload structure before sending.
        Ensures each channel has required payload fields for successful delivery.
        
        Args:
            notification: NotificationQueue instance to validate
            
        Returns:
            bool: True if notification is valid for sending, False otherwise
            
        Validation Rules:
            - Email: requires subject, body, recipient
            - WhatsApp: requires message, recipient
            - Payload must be a valid dictionary
        """
        valid_channels = {"email", "whatsapp"}
        if notification.channel not in valid_channels:
            return False
        # Channel-specific payload validation
        if notification.channel == "email":
            required_keys = {"subject", "body", "recipient"}
        elif notification.channel == "whatsapp":
            required_keys = {"message", "recipient"}
        else:
            required_keys = set()
        if not isinstance(notification.payload, dict):
            return False
        if not required_keys.issubset(notification.payload.keys()):
            return False
        return True
