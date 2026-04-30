import logging
import json
import random
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SimulatedSMSProvider:
    """
    Simulates an SMS gateway response.

    Behaves realistically:
    - Logs the full payload that would be sent to a real API
    - Returns a response shape identical to Africa's Talking
    - Randomly simulates a 10% failure rate to test retry logic
    - Introduces a simulated message ID for traceability
    """

    FAILURE_RATE = 0.10   # 10% chance of simulated failure

    def send(self, payload: dict) -> dict:
        """
        payload = {
            'to':        '+254712345678',
            'message':   'Your delivery is on the way.',
            'sender_id': 'NOTIFLOW',
        }
        """
        logger.info("=" * 60)
        logger.info("📱 SIMULATED SMS — would send to Safaricom gateway")
        logger.info(f"  To:        {payload['to']}")
        logger.info(f"  From:      {payload.get('sender_id', 'NOTIFLOW')}")
        logger.info(f"  Message:   {payload['message']}")
        logger.info(f"  Chars:     {len(payload['message'])} / 160")
        logger.info(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("=" * 60)

        # Simulate occasional network/gateway failure
        if random.random() < self.FAILURE_RATE:
            return self._failure_response(payload)

        return self._success_response(payload)

    def _success_response(self, payload: dict) -> dict:
        message_id = f"SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        return {
            'SMSMessageData': {
                'Message': 'Sent to 1/1 Total Cost: KES 1.00',
                'Recipients': [
                    {
                        'statusCode': 101,
                        'number':     payload['to'],
                        'status':     'Success',
                        'cost':       'KES 1.0000',
                        'messageId':  message_id,
                    }
                ]
            }
        }

    def _failure_response(self, payload: dict) -> dict:
        """Simulate a realistic gateway rejection."""
        errors = [
            {'statusCode': 403, 'status': 'InvalidSenderId',
             'description': 'Sender ID not registered with carrier.'},
            {'statusCode': 500, 'status': 'GatewayError',
             'description': 'Upstream gateway timeout. Retry recommended.'},
            {'statusCode': 402, 'status': 'InsufficientBalance',
             'description': 'Account balance too low to send message.'},
        ]
        error = random.choice(errors)
        logger.warning(f"Simulated SMS failure: {error['status']} — {error['description']}")
        return {
            'SMSMessageData': {
                'Message': error['description'],
                'Recipients': [
                    {
                        'statusCode': error['statusCode'],
                        'number':     payload['to'],
                        'status':     error['status'],
                        'cost':       'KES 0',
                        'messageId':  None,
                    }
                ]
            }
        }