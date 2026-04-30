import logging
from background_task import background
from background_task.models import Task

logger = logging.getLogger(__name__)


@background(schedule=0)
def dispatch_notification(notification_id: str):
    """
    Background task: load notification, dispatch, and handle retry on failure.
    """
    from .models import Notification
    from .services.dispatcher import NotificationDispatcher
    from .services.retry_manager import RetryManager

    logger.info(f"[Task] Starting dispatch for notification_id={notification_id}")

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"[Task] Notification {notification_id} not found. Skipping.")
        return

    # Guard against duplicate delivery on task retry
    if notification.status == Notification.Status.SENT:
        logger.warning(f"[Task] {notification_id} already SENT. Skipping.")
        return

    dispatcher = NotificationDispatcher()
    success    = dispatcher.dispatch(notification)

    if success:
        logger.info(f"[Task] Dispatch succeeded for {notification_id}")
        return

    # Fetch latest error from the log just written by the dispatcher
    last_log = notification.logs.order_by('-attempted_at').first()
    error_message = last_log.error_message if last_log else None

    logger.warning(
        f"[Task] Dispatch failed for {notification_id}. "
        f"Error: {error_message}"
    )

    # Delegate retry decision to RetryManager
    retry_manager = RetryManager()
    retrying = retry_manager.handle_failure(notification, error_message)

    if not retrying:
        logger.warning(
            f"[Task] No further retries for {notification_id}. "
            f"Final status: {notification.status}"
        )


def enqueue_notification(notification_id: str, delay_seconds: int = 0):
    """Enqueue a notification for background delivery."""
    dispatch_notification(
        str(notification_id),
        schedule=delay_seconds,
    )
    logger.info(
        f"[Queue] Enqueued notification_id={notification_id} "
        f"with delay={delay_seconds}s"
    )


def get_queue_stats() -> dict:
    """Returns a snapshot of queue health."""
    from django.utils import timezone

    total   = Task.objects.count()
    overdue = Task.objects.filter(run_at__lt=timezone.now()).count()

    return {
        'queued':  total,
        'overdue': overdue,
    }