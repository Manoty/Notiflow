import logging
from .failure_classifier import FailureClassifier
from .backoff import ExponentialBackoff

logger = logging.getLogger(__name__)


class RetryManager:
    """
    Decides whether to retry a failed notification and schedules it.
    Called by the background task after a failed dispatch attempt.

    This is intentionally separate from the dispatcher so each class
    has one responsibility:
        Dispatcher   → try to deliver
        RetryManager → decide what to do after failure
    """

    def handle_failure(self, notification, error_message: str | None) -> bool:
        """
        Evaluates a failed notification and either:
            - Re-enqueues it with a backoff delay, or
            - Marks it permanently failed and stops.

        Returns True if a retry was scheduled, False if giving up.
        """
        # Import here to avoid circular dependency with tasks.py
        from ..tasks import enqueue_notification

        notification_id = str(notification.id)

        # Step 1: Is this error worth retrying at all?
        if not FailureClassifier.is_transient(error_message):
            logger.warning(
                f"[Retry] Permanent failure for {notification_id}. "
                f"Error: {error_message}. No retry scheduled."
            )
            self._log_giving_up(notification, reason="permanent_error")
            return False

        # Step 2: Have we exhausted retries?
        if not notification.can_retry:
            logger.warning(
                f"[Retry] Max retries reached for {notification_id} "
                f"({notification.retry_count}/{notification.max_retries}). "
                "Giving up."
            )
            self._log_giving_up(notification, reason="max_retries_exceeded")
            return False

        # Step 3: Calculate backoff — next attempt number is current count + 1
        next_attempt = notification.retry_count + 1
        delay        = ExponentialBackoff.delay_for_attempt(next_attempt)

        logger.info(
            f"[Retry] Scheduling retry #{next_attempt} for {notification_id} "
            f"in {delay}s "
            f"(attempt {notification.retry_count}/{notification.max_retries})"
        )

        enqueue_notification(notification_id, delay_seconds=delay)
        return True

    def _log_giving_up(self, notification, reason: str):
        """Write a final log entry explaining why we stopped retrying."""
        from ..models import NotificationLog

        NotificationLog.objects.create(
            notification   = notification,
            attempt_number = notification.retry_count,
            status         = NotificationLog.Status.FAILURE,
            response_data  = None,
            error_message  = (
                f"Retry abandoned: {reason}. "
                f"Total attempts: {notification.retry_count}/{notification.max_retries}."
            ),
        )