import requests
import logging
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NotificationResult:
    """
    Returned from every NotiflowClient call.
    Gives the caller structured access to outcome data
    without parsing raw HTTP responses.
    """
    success:         bool
    notification_id: Optional[str] = None
    status:          Optional[str] = None
    channel:         Optional[str] = None
    error:           Optional[str] = None
    raw_response:    Optional[dict] = field(default=None, repr=False)

    def __str__(self):
        if self.success:
            return (
                f"✓ Notification queued | "
                f"id={self.notification_id} channel={self.channel}"
            )
        return f"✗ Notification failed | error={self.error}"


class NotiflowClient:
    """
    HTTP client for the Notiflow notification service.

    Usage:
        client = NotiflowClient(app_id='tixora')
        result = client.send_email(
            user_id = 'user@example.com',
            title   = 'Booking Confirmed',
            message = 'Your ticket is ready.',
        )
        if result.success:
            print(f"Queued: {result.notification_id}")

    The client is intentionally thin — it handles HTTP mechanics,
    error wrapping, and logging. Business logic stays in the caller.
    """

    DEFAULT_TIMEOUT = 10   # seconds

    def __init__(
        self,
        app_id:   str,
        base_url: str = 'http://127.0.0.1:8000',
        api_key:  Optional[str] = None,     
        timeout:  int = 10,
    ):
        self.app_id   = app_id
        self.base_url = base_url.rstrip('/')
        self.timeout  = timeout
        self.session  = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-App-ID':     app_id,          # identify caller in server logs
        })
        if api_key:
            self.session.headers['X-API-Key'] = api_key

    # ── Public channel methods ─────────────────────────────────────────────

    def send_email(
        self,
        user_id:     str,
        title:       str,
        message:     str,
        max_retries: int = 3,
        scheduled_at: Optional[datetime] = None,
    ) -> NotificationResult:
        return self._send(
            user_id=user_id,
            channel='email',
            title=title,
            message=message,
            max_retries=max_retries,
            scheduled_at=scheduled_at,
        )

    def send_sms(
        self,
        user_id:     str,
        title:       str,
        message:     str,
        max_retries: int = 3,
    ) -> NotificationResult:
        return self._send(
            user_id=user_id,
            channel='sms',
            title=title,
            message=message,
            max_retries=max_retries,
        )

    def send_in_app(
        self,
        user_id:     str,
        title:       str,
        message:     str,
    ) -> NotificationResult:
        return self._send(
            user_id=user_id,
            channel='in_app',
            title=title,
            message=message,
            max_retries=1,   # in-app is instant — one attempt only
        )

    def send_all_channels(
        self,
        user_id:        str,
        title:          str,
        message:        str,
        email_address:  Optional[str] = None,
        phone_number:   Optional[str] = None,
    ) -> list[NotificationResult]:
        """
        Convenience method: send the same notification across all
        three channels simultaneously. Returns a result per channel.
        """
        results = []

        email_uid = email_address or user_id
        results.append(self.send_email(email_uid, title, message))

        phone_uid = phone_number or user_id
        results.append(self.send_sms(phone_uid, title, message))

        results.append(self.send_in_app(user_id, title, message))

        return results

    def get_notification(self, notification_id: str) -> Optional[dict]:
        """Fetch a notification's current status and log history."""
        try:
            response = self.session.get(
                f"{self.base_url}/notifications/{notification_id}/",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"[NotiflowClient] Failed to fetch {notification_id}: {e}")
            return None

    def get_inbox(self, user_id: str, unread_only: bool = False) -> Optional[dict]:
        """Fetch in-app inbox for a user."""
        try:
            params = {'user_id': user_id, 'app_id': self.app_id}
            if unread_only:
                params['unread_only'] = 'true'
            response = self.session.get(
                f"{self.base_url}/notifications/inbox/",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"[NotiflowClient] Failed to fetch inbox for {user_id}: {e}")
            return None

    def get_unread_count(self, user_id: str) -> int:
        """Returns the unread in-app count for a user, or 0 on error."""
        try:
            response = self.session.get(
                f"{self.base_url}/notifications/unread-count/",
                params={'user_id': user_id, 'app_id': self.app_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get('unread_count', 0)
        except requests.RequestException as e:
            logger.error(f"[NotiflowClient] Failed to fetch unread count: {e}")
            return 0

    # ── Private core ──────────────────────────────────────────────────────

    def _send(
        self,
        user_id:      str,
        channel:      str,
        title:        str,
        message:      str,
        max_retries:  int = 3,
        scheduled_at: Optional[datetime] = None,
    ) -> NotificationResult:

        payload = {
            'user_id':     user_id,
            'app_id':      self.app_id,
            'channel':     channel,
            'title':       title,
            'message':     message,
            'max_retries': max_retries,
        }
        if scheduled_at:
            payload['scheduled_at'] = scheduled_at.isoformat()

        try:
            response = self.session.post(
                f"{self.base_url}/notifications/send/",
                json=payload,
                timeout=self.timeout,
            )

            data = response.json()

            if response.status_code == 202:
                logger.info(
                    f"[NotiflowClient:{self.app_id}] Queued {channel} "
                    f"for {user_id} | id={data.get('notification_id')}"
                )
                return NotificationResult(
                    success         = True,
                    notification_id = data.get('notification_id'),
                    status          = data.get('status'),
                    channel         = channel,
                    raw_response    = data,
                )
            else:
                error_msg = str(data.get('errors') or data.get('error') or data)
                logger.warning(
                    f"[NotiflowClient:{self.app_id}] API rejected {channel} "
                    f"for {user_id} | status={response.status_code} | {error_msg}"
                )
                return NotificationResult(
                    success      = False,
                    error        = error_msg,
                    raw_response = data,
                )

        except requests.Timeout:
            msg = f"Notiflow API timed out after {self.timeout}s"
            logger.error(f"[NotiflowClient:{self.app_id}] {msg}")
            return NotificationResult(success=False, error=msg)

        except requests.ConnectionError:
            msg = "Could not connect to Notiflow API. Is it running?"
            logger.error(f"[NotiflowClient:{self.app_id}] {msg}")
            return NotificationResult(success=False, error=msg)

        except requests.RequestException as e:
            msg = f"Unexpected HTTP error: {str(e)}"
            logger.error(f"[NotiflowClient:{self.app_id}] {msg}")
            return NotificationResult(success=False, error=msg)