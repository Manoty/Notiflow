import logging
from background_task import background
from background_task.models import Task

logger = logging.getLogger(__name__)


@background(schedule=0)
def dispatch_notification(notification_id: str):
    """
    Background task: load a notification by ID and dispatch it.

    Decorated with @background so calling dispatch_notification(id)
    enqueues it immediately (schedule=0 means run as soon as possible).
    The worker picks it up within its poll interval.

    Why pass the ID instead of the object?
    Tasks are serialised to JSON for storage. A UUID string
    survives serialisation perfectly. A Django model instance
    does not — by the time the worker runs, the object could
    be stale anyway.
    """
    # Import here to avoid circular imports at module load
    from .models import Notification
    from .services.dispatcher import NotificationDispatcher

    logger.info(f"[Task] Starting dispatch for notification_id={notification_id}")

    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(
            f"[Task] Notification {notification_id} not found. "
            "It may have been deleted before the task ran."
        )
        return

    # Guard: don't re-dispatch an already-sent notification
    # This matters if the task is retried after a partial failure
    if notification.status == Notification.Status.SENT:
        logger.warning(
            f"[Task] Notification {notification_id} already SENT. "
            "Skipping to avoid duplicate delivery."
        )
        return

    dispatcher = NotificationDispatcher()
    success = dispatcher.dispatch(notification)

    if success:
        logger.info(f"[Task] Dispatch succeeded for {notification_id}")
    else:
        logger.warning(
            f"[Task] Dispatch failed for {notification_id} "
            f"(attempt {notification.retry_count}/{notification.max_retries})"
        )
        # Phase 8 retry logic reads can_retry and re-enqueues if appropriate


def enqueue_notification(notification_id: str, delay_seconds: int = 0):
    """
    Wrapper around dispatch_notification that makes call sites cleaner
    and gives us one place to add scheduling logic later
    (e.g. honour notification.scheduled_at).
    """
    dispatch_notification(
        str(notification_id),
        schedule=delay_seconds,
    )
    logger.info(
        f"[Queue] Enqueued notification_id={notification_id} "
        f"with delay={delay_seconds}s"
    )


def get_queue_stats() -> dict:
    """
    Returns a snapshot of queue health.
    Used by the admin dashboard and health-check endpoint.
    """
    from django.utils import timezone

    total   = Task.objects.count()
    overdue = Task.objects.filter(run_at__lt=timezone.now()).count()

    return {
        'queued':  total,
        'overdue': overdue,
    }