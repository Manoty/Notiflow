import logging

logger = logging.getLogger(__name__)


class InAppService:
    """
    In-app notification delivery.

    Unlike Email and SMS, delivery here is a DB write —
    the Notification record IS the notification.
    The service marks it 'sent' immediately and logs the attempt.

    The frontend then reads it via the inbox endpoints.
    """

    def send(self, notification) -> dict:
        """
        For in-app, the notification already exists in the DB
        (created by the dispatcher before calling send).
        We just confirm it's ready for the frontend to consume.
        """
        try:
            logger.info(
                f"In-app notification stored | id={notification.id} "
                f"| user={notification.user_id} | app={notification.app_id}"
            )
            return {
                'success':  True,
                'response': (
                    f"In-app notification ready for user '{notification.user_id}' "
                    f"in app '{notification.app_id}'"
                ),
                'error': None,
            }

        except Exception as e:
            msg = f"Unexpected error storing in-app notification: {str(e)}"
            logger.exception(msg)
            return {'success': False, 'response': None, 'error': msg}