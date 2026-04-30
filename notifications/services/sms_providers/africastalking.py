import logging
import json
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# When ready:  pip install africastalking
# This stub shows exactly what the live integration looks like
# so Phase 9 is a drop-in swap with no structural changes.


class AfricasTalkingProvider:
    """
    Live Safaricom SMS via Africa's Talking gateway.
    Activate by setting SMS_PROVIDER=africastalking in .env
    and providing AT_USERNAME + AT_API_KEY.

    Africa's Talking is the standard Safaricom-compatible SMS
    aggregator for Kenya — used by M-Pesa integrations,
    delivery platforms, and ticketing systems across East Africa.
    """

    BASE_URL = "https://api.africastalking.com/version1/messaging"
    SANDBOX_URL = "https://api.sandbox.africastalking.com/version1/messaging"

    def __init__(self):
        self.username  = settings.AT_USERNAME
        self.api_key   = settings.AT_API_KEY
        self.sender_id = settings.SMS_SENDER_ID
        # Use sandbox when DEBUG=True, production otherwise
        self.url = self.SANDBOX_URL if settings.DEBUG else self.BASE_URL

    def send(self, payload: dict) -> dict:
        headers = {
            'apiKey':       self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept':       'application/json',
        }
        data = {
            'username': self.username,
            'to':       payload['to'],
            'message':  payload['message'],
            'from':     self.sender_id,
        }

        try:
            response = requests.post(
                self.url,
                headers=headers,
                data=data,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            return {
                'SMSMessageData': {
                    'Message': 'Request timed out after 10 seconds.',
                    'Recipients': [{'status': 'GatewayTimeout', 'statusCode': 408}]
                }
            }
        except requests.RequestException as e:
            return {
                'SMSMessageData': {
                    'Message': str(e),
                    'Recipients': [{'status': 'RequestError', 'statusCode': 500}]
                }
            }