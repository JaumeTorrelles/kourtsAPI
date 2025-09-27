
import asyncio
from datetime import datetime
from app.models.notification import NotificationQueue
from sqlmodel import Session
from typing import List

class NotificationWorker:
    """
    Enterprise-grade async notification worker for background job processing.
    
    Features:
    - Intelligent processing strategy (sequential vs parallel based on batch size)
    - Multi-channel support (email, WhatsApp) with pluggable clients
    - Advanced retry logic with attempt tracking and max limits
    - Production-ready error handling with transaction safety
    - Configurable parallel processing threshold
    
    Architecture:
        This worker consumes jobs from the NotificationService queue and processes
        them asynchronously. It adapts processing strategy based on workload size
        to optimize performance while preventing system overload.
    """
    def __init__(self, service, email_client=None, whatsapp_client=None, logger=None):
        """
        Initializes the notification worker with pluggable dependencies.
        
        Args:
            service: NotificationService instance for database operations
            email_client: Optional email provider client (e.g., SendGrid, AWS SES)
            whatsapp_client: Optional WhatsApp provider client (e.g., Twilio, WhatsApp Business API)
            logger: Optional logger instance for error tracking and debugging
            
        Design Pattern:
            Uses dependency injection to allow different providers without code changes
        """
        self.service = service
        self.email_client = email_client
        self.whatsapp_client = whatsapp_client
        self.logger = logger

    async def _send_notification(self, notification, session: Session):
        """
        Processes a single notification with comprehensive error handling and retry logic.
        
        Args:
            notification: NotificationQueue instance to process
            session: Database session for updating notification status
            
        Returns:
            NotificationQueue: Updated notification with new status
            
        Status Flow:
            PENDING -> SENT (success) | FAILED (max attempts) | PENDING (retry)
            
        Retry Logic:
            - Validates payload before sending
            - Increments attempt counter on failures  
            - Marks as FAILED when max_attempts reached
            - Maintains PENDING status for retries
        """
        try:
            if not self.service.validate_notification(notification):
                notification.status = "invalid"
            else:
                success = False
                if notification.channel == "email":
                    success = await self._async_send_email(notification.payload)
                elif notification.channel == "whatsapp":
                    success = await self._async_send_whatsapp(notification.payload)
                if success:
                    notification.status = "sent"
                    notification.sent_at = datetime.utcnow()
                else:
                    notification.attempts += 1
                    if notification.attempts >= notification.max_attempts:
                        notification.status = "failed"
                    else:
                        notification.status = "pending"
        except Exception as e:
            notification.attempts += 1
            if notification.attempts >= notification.max_attempts:
                notification.status = "failed"
            else:
                notification.status = "pending"
            if self.logger:
                self.logger.exception(f"Error processing notification {notification.id}: {e}")
        session.add(notification)
        return notification

    async def _async_send_email(self, payload: dict) -> bool:
        """
        Sends email notification using the configured email client.
        
        Args:
            payload: Email payload containing subject, body, recipient
            
        Returns:
            bool: True if email sent successfully, False otherwise
            
        Integration Point:
            Replace the mock implementation with actual email provider:
            - SendGrid: await self.email_client.send_email(payload)
            - AWS SES: await self.email_client.send_email(payload) 
            - SMTP: await self.email_client.send_email(payload)
        """
        try:
            await asyncio.sleep(0.1)  # Mock delay - replace with actual email provider
            # await self.email_client.send_email(payload)
            return True
        except Exception:
            return False

    async def _async_send_whatsapp(self, payload: dict) -> bool:
        """
        Sends WhatsApp notification using the configured WhatsApp client.
        
        Args:
            payload: WhatsApp payload containing message, recipient
            
        Returns:
            bool: True if message sent successfully, False otherwise
            
        Integration Point:
            Replace the mock implementation with actual WhatsApp provider:
            - Twilio: await self.whatsapp_client.send_message(payload)
            - WhatsApp Business API: await self.whatsapp_client.send_message(payload)
            - Meta Cloud API: await self.whatsapp_client.send_message(payload)
        """
        try:
            await asyncio.sleep(0.1)  # Mock delay - replace with actual WhatsApp provider
            # await self.whatsapp_client.send_message(payload)
            return True
        except Exception:
            return False

    async def send_pending_notifications(self, parallel_threshold: int = 10):
        """
        Intelligently processes pending notifications using adaptive strategy.
        Uses sequential processing for small batches, parallel processing for large ones.
        
        Args:
            parallel_threshold: Batch size threshold to switch from sequential to parallel (default: 10)
            
        Processing Strategy:
            - Small batches (≤ threshold): Sequential processing to minimize overhead
            - Large batches (> threshold): Parallel processing for maximum throughput
            
        Transaction Safety:
            - All notifications in batch are committed together
            - Automatic rollback on batch commit failures  
            - Individual notification status updates are preserved in memory
            
        Performance Benefits:
            - Sequential: Lower memory usage, simpler debugging, fewer race conditions
            - Parallel: Higher throughput, better resource utilization for large batches
        """
        notifications: List[NotificationQueue] = self.service.get_pending_notifications()
        session: Session = self.service.session
        results = []
        
        if len(notifications) <= parallel_threshold:
            # Sequential processing for small batches - lower overhead, easier debugging
            for n in notifications:
                result = await self._send_notification(n, session)
                results.append(result)
        else:
            # Parallel processing for large batches - maximum throughput
            tasks = [self._send_notification(n, session) for n in notifications]
            results = await asyncio.gather(*tasks)
            
        # Batch commit for transaction safety
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            if self.logger:
                self.logger.exception(f"Error committing notifications batch: {e}")
        
        return results
