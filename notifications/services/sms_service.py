import logging
import json
from django.conf import settings
from .sms_providers.simulated import SimulatedSMSProvider
from .sms_providers.africastalking import AfricasTalkingProvider

logger = logging.getLogger(__name__)


class SMSService:
    """
    Channel service for SMS delivery.
    Mirrors EmailService's interface: accepts a Notification,
    returns a result dict with success, response, error.

    Provider is selected via SMS_PROVIDER in settings:
        'simulated'      → SimulatedSMSProvider (default)
        'africastalking' → AfricasTalkingProvider (live)
    """

    SUCCESS_CODES = {101, 200}   # Africa's Talking success status codes

    def __init__(self):
        provider_name = getattr(settings, 'SMS_PROVIDER', 'simulated')
        self.provider = self._load_provider(provider_name)
        logger.info(f"SMSService initialised with provider: {provider_name}")

    def send(self, notification) -> dict:
        phone = self._resolve_phone(notification)

        if not phone:
            return {
                'success':  False,
                'response': None,
                'error':    (
                    f"Cannot resolve phone number for user_id '{notification.user_id}'. "
                    "Implement identity resolution in Phase 9."
                ),
            }

        if not self._validate_phone(phone):
            return {
                'success':  False,
                'response': None,
                'error':    f"Invalid phone format: '{phone}'. Expected E.164 e.g. +254712345678",
            }

        payload = self._build_payload(notification, phone)

        try:
            raw_response = self.provider.send(payload)
            return self._parse_response(raw_response, notification)

        except Exception as e:
            msg = f"SMS provider raised unexpected exception: {str(e)}"
            logger.exception(msg)
            return {'success': False, 'response': None, 'error': msg}

    # ── Private helpers ────────────────────────────────────────────────────

    def _load_provider(self, name: str):
        providers = {
            'simulated':      SimulatedSMSProvider,
            'africastalking': AfricasTalkingProvider,
        }
        cls = providers.get(name)
        if not cls:
            raise ValueError(
                f"Unknown SMS provider '{name}'. "
                f"Choose from: {list(providers.keys())}"
            )
        return cls()

    def _resolve_phone(self, notification) -> str | None:
        """
        Resolve phone number from user_id.
        If user_id looks like an E.164 number, use it directly.
        Otherwise return None — Phase 9 will implement real lookup.
        """
        uid = notification.user_id.strip()
        if uid.startswith('+') and uid[1:].isdigit():
            return uid
        # Kenyan number without country code e.g. '0712345678'
        if uid.startswith('0') and len(uid) == 10 and uid[1:].isdigit():
            return '+254' + uid[1:]
        logger.warning(
            f"user_id '{uid}' is not a phone number. "
            "SMS delivery skipped pending identity resolution."
        )
        return None

    def _validate_phone(self, phone: str) -> bool:
        """E.164 format: + followed by 7–15 digits."""
        return (
            phone.startswith('+')
            and phone[1:].isdigit()
            and 7 <= len(phone[1:]) <= 15
        )

    def _build_payload(self, notification, phone: str) -> dict:
        """
        Construct the SMS payload.
        SMS has a 160-char limit per message segment.
        Warn if the message will be split into multiple segments.
        """
        message = f"{notification.title}: {notification.message}"

        if len(message) > 160:
            segments = -(-len(message) // 160)  # ceiling division
            logger.warning(
                f"SMS message is {len(message)} chars — "
                f"will be sent as {segments} segments (cost x{segments}). "
                "Consider shortening the message."
            )

        return {
            'to':        phone,
            'message':   message,
            'sender_id': getattr(settings, 'SMS_SENDER_ID', 'NOTIFLOW'),
        }

    def _parse_response(self, raw: dict, notification) -> dict:
        """
        Parse Africa's Talking response shape.
        Both SimulatedSMSProvider and AfricasTalkingProvider
        return this same structure, so parsing is identical.
        """
        try:
            recipients = raw['SMSMessageData']['Recipients']
            if not recipients:
                return {
                    'success':  False,
                    'response': json.dumps(raw),
                    'error':    'Gateway returned empty recipients list.',
                }

            recipient = recipients[0]
            status_code = recipient.get('statusCode', 0)
            gateway_status = recipient.get('status', 'Unknown')
            message_id = recipient.get('messageId')

            if status_code in self.SUCCESS_CODES:
                logger.info(
                    f"SMS delivered | notification={notification.id} "
                    f"| messageId={message_id} | to={recipient.get('number')}"
                )
                return {
                    'success':  True,
                    'response': (
                        f"Delivered | messageId={message_id} "
                        f"| cost={recipient.get('cost', 'N/A')}"
                    ),
                    'error': None,
                }
            else:
                logger.warning(
                    f"SMS not delivered | notification={notification.id} "
                    f"| status={gateway_status} | code={status_code}"
                )
                return {
                    'success':  False,
                    'response': json.dumps(raw),
                    'error':    f"Gateway rejected: {gateway_status} (code {status_code})",
                }

        except (KeyError, IndexError, TypeError) as e:
            return {
                'success':  False,
                'response': json.dumps(raw),
                'error':    f"Failed to parse gateway response: {str(e)}",
            }