import logging
from django.utils import timezone
from ..models import Notification, NotificationLog
from .email_service import EmailService
from .sms_service import SMSService
from .inapp_service import InAppService

logger = logging.getLogger(__name__)


class NotificationDispatcher:
    """
    Single entry point for all notification delivery.
    The view (and background task) calls dispatch(notification).
    The dispatcher routes to the correct channel service,
    then writes a NotificationLog regardless of outcome.
    """

    def __init__(self):
        self.services = {
            Notification.Channel.EMAIL:  EmailService(),
            Notification.Channel.SMS:   SMSService(),
            Notification.Channel.IN_APP: InAppService(), 
        }

    def dispatch(self, notification: Notification) -> bool:
        """
        Route and deliver a notification.
        Updates notification status and writes a log entry.
        Returns True on success, False on failure.
        """
        service = self.services.get(notification.channel)

        if not service:
            self._write_log(
                notification,
                success=False,
                error=f"No service registered for channel '{notification.channel}'."
            )
            self._mark_failed(notification)
            return False

        # Increment attempt counter before trying
        notification.retry_count += 1
        notification.save(update_fields=['retry_count', 'updated_at'])

        result = service.send(notification)

        self._write_log(
            notification,
            success=result['success'],
            response=result.get('response'),
            error=result.get('error'),
            attempt_number=notification.retry_count,
        )

        if result['success']:
            self._mark_sent(notification)
        else:
            self._mark_failed(notification)

        return result['success']

    # ── Private helpers ────────────────────────────────────────────────────

    def _mark_sent(self, notification: Notification):
        notification.status = Notification.Status.SENT
        notification.save(update_fields=['status', 'updated_at'])
        logger.info(f"Notification {notification.id} marked SENT")

    def _mark_failed(self, notification: Notification):
        notification.status = Notification.Status.FAILED
        notification.save(update_fields=['status', 'updated_at'])
        logger.warning(
            f"Notification {notification.id} marked FAILED "
            f"(attempt {notification.retry_count}/{notification.max_retries})"
        )

    def _write_log(
        self,
        notification: Notification,
        success: bool,
        response: str = None,
        error: str = None,
        attempt_number: int = 1,
    ):
        NotificationLog.objects.create(
            notification   = notification,
            attempt_number = attempt_number,
            status = (
                NotificationLog.Status.SUCCESS
                if success else
                NotificationLog.Status.FAILURE
            ),
            response_data = response,
            error_message = error,
        )