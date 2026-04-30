"""
Tixora Notification Triggers
─────────────────────────────
These functions are called by Tixora's business logic at key moments
in the ticket purchase and event lifecycle.

A Tixora developer would call these directly — they don't interact
with Notiflow's internals at all. The NotiflowClient handles all HTTP.

Example usage inside Tixora's order service:
    from integrations.tixora.notification_triggers import on_ticket_purchased
    on_ticket_purchased(order)
"""

import logging
from datetime import datetime, timedelta, timezone
from integrations.notiflow_client import NotiflowClient, NotificationResult
import os

logger = logging.getLogger(__name__)

# One client instance per app — reuses the HTTP session
_client = NotiflowClient(
    app_id  = 'tixora',
    api_key = os.getenv('TIXORA_API_KEY'),
)

# ── Data shapes (simulating Tixora's models) ──────────────────────────────

class TicketOrder:
    """Simulates a Tixora order object."""
    def __init__(
        self,
        order_id:       str,
        user_id:        str,
        user_email:     str,
        user_phone:     str,
        event_name:     str,
        event_date:     str,
        event_venue:    str,
        ticket_count:   int,
        total_amount:   str,
    ):
        self.order_id     = order_id
        self.user_id      = user_id
        self.user_email   = user_email
        self.user_phone   = user_phone
        self.event_name   = event_name
        self.event_date   = event_date
        self.event_venue  = event_venue
        self.ticket_count = ticket_count
        self.total_amount = total_amount


# ── Trigger functions ─────────────────────────────────────────────────────

def on_ticket_purchased(order: TicketOrder) -> dict:
    """
    Triggered when a ticket purchase is confirmed.
    Sends email + in-app notification.
    SMS is omitted on purchase — used for day-of reminders only.

    Returns a summary of which notifications succeeded.
    """
    logger.info(
        f"[Tixora] Ticket purchase trigger | "
        f"order={order.order_id} user={order.user_id}"
    )

    title   = f"Ticket Confirmed — {order.event_name}"
    message = (
        f"Your booking is confirmed! Here are your details:\n\n"
        f"Event:   {order.event_name}\n"
        f"Date:    {order.event_date}\n"
        f"Venue:   {order.event_venue}\n"
        f"Tickets: {order.ticket_count}\n"
        f"Total:   {order.total_amount}\n\n"
        f"Order reference: {order.order_id}\n"
        f"Show this confirmation at the entrance. See you there!"
    )

    results = {}

    # Email: primary confirmation channel
    results['email'] = _client.send_email(
        user_id = order.user_email,
        title   = title,
        message = message,
    )

    # In-app: instant notification in the Tixora app
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"Your {order.ticket_count} ticket(s) for {order.event_name} are confirmed.",
    )

    _log_results('on_ticket_purchased', results, order.order_id)
    return results


def on_event_reminder(order: TicketOrder, hours_before: int = 24) -> dict:
    """
    Triggered by a scheduled job N hours before the event.
    Sends SMS + in-app reminder. Email omitted — avoid fatigue.
    """
    logger.info(
        f"[Tixora] Event reminder trigger | "
        f"order={order.order_id} hours_before={hours_before}"
    )

    title   = f"Reminder: {order.event_name} is {'tomorrow' if hours_before == 24 else f'in {hours_before}h'}"
    message = (
        f"{order.event_name} | {order.event_date} | {order.event_venue}. "
        f"Gates open 1 hour before the event. Have your ticket QR ready."
    )

    results = {}

    # SMS: high-visibility channel for day-of reminders
    results['sms'] = _client.send_sms(
        user_id = order.user_phone,
        title   = title,
        message = message,
    )

    # In-app: banner reminder in the app
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = message,
    )

    _log_results('on_event_reminder', results, order.order_id)
    return results


def on_ticket_cancelled(order: TicketOrder, reason: str = '') -> dict:
    """Triggered when a ticket is cancelled or refunded."""
    logger.info(f"[Tixora] Cancellation trigger | order={order.order_id}")

    title   = f"Booking Cancelled — {order.event_name}"
    message = (
        f"Your booking for {order.event_name} has been cancelled.\n"
        f"Refund of {order.total_amount} will appear in 3–5 business days."
    )
    if reason:
        message += f"\nReason: {reason}"

    results = {}

    results['email'] = _client.send_email(
        user_id = order.user_email,
        title   = title,
        message = message,
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"Your booking for {order.event_name} has been cancelled. Refund in 3–5 days.",
    )

    _log_results('on_ticket_cancelled', results, order.order_id)
    return results


# ── Private helpers ────────────────────────────────────────────────────────

def _log_results(trigger: str, results: dict, reference: str):
    for channel, result in results.items():
        if result.success:
            logger.info(
                f"[Tixora:{trigger}] {channel} queued | "
                f"ref={reference} | id={result.notification_id}"
            )
        else:
            logger.error(
                f"[Tixora:{trigger}] {channel} FAILED | "
                f"ref={reference} | error={result.error}"
            )