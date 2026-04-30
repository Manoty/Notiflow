"""
Scott Delivery Notification Triggers
──────────────────────────────────────
Called by Scott's order and delivery management services at key
moments in the delivery lifecycle.
"""

import logging
from integrations.notiflow_client import NotiflowClient

logger = logging.getLogger(__name__)

_client = NotiflowClient(app_id='scott')


class DeliveryOrder:
    """Simulates a Scott Delivery order object."""
    def __init__(
        self,
        order_id:          str,
        user_id:           str,
        user_email:        str,
        user_phone:        str,
        recipient_name:    str,
        delivery_address:  str,
        item_description:  str,
        tracking_code:     str,
        estimated_arrival: str,
    ):
        self.order_id          = order_id
        self.user_id           = user_id
        self.user_email        = user_email
        self.user_phone        = user_phone
        self.recipient_name    = recipient_name
        self.delivery_address  = delivery_address
        self.item_description  = item_description
        self.tracking_code     = tracking_code
        self.estimated_arrival = estimated_arrival


def on_order_placed(order: DeliveryOrder) -> dict:
    """Triggered when a delivery order is created."""
    logger.info(f"[Scott] Order placed trigger | order={order.order_id}")

    title   = "Delivery Order Received"
    message = (
        f"Hi {order.recipient_name}, your delivery order has been received.\n\n"
        f"Item:      {order.item_description}\n"
        f"Address:   {order.delivery_address}\n"
        f"Tracking:  {order.tracking_code}\n"
        f"ETA:       {order.estimated_arrival}"
    )

    results = {}

    results['email'] = _client.send_email(
        user_id = order.user_email,
        title   = title,
        message = message,
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"Order {order.tracking_code} received. ETA: {order.estimated_arrival}",
    )

    _log_results('on_order_placed', results, order.order_id)
    return results


def on_order_dispatched(order: DeliveryOrder, rider_name: str) -> dict:
    """
    Triggered when a rider picks up the package.
    SMS is the primary channel — highest open rate when
    the customer is waiting for a delivery.
    """
    logger.info(f"[Scott] Dispatch trigger | order={order.order_id}")

    title   = "Your Package is On the Way"
    message = (
        f"Your delivery ({order.item_description}) has been picked up by {rider_name} "
        f"and is on the way to {order.delivery_address}. "
        f"ETA: {order.estimated_arrival}. Tracking: {order.tracking_code}"
    )

    results = {}

    # SMS: primary — customer needs to know immediately
    results['sms'] = _client.send_sms(
        user_id = order.user_phone,
        title   = title,
        message = message,
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"{rider_name} is heading your way. ETA: {order.estimated_arrival}",
    )

    _log_results('on_order_dispatched', results, order.order_id)
    return results


def on_delivery_nearby(order: DeliveryOrder, stops_away: int) -> dict:
    """Triggered when the rider is N stops from the destination."""
    logger.info(f"[Scott] Nearby trigger | order={order.order_id} stops={stops_away}")

    title   = f"Delivery Arriving Soon — {stops_away} Stop{'s' if stops_away != 1 else ''} Away"
    message = (
        f"Your delivery is {stops_away} stop{'s' if stops_away != 1 else ''} away. "
        f"Please be available at {order.delivery_address}."
    )

    results = {}

    results['sms'] = _client.send_sms(
        user_id = order.user_phone,
        title   = title,
        message = message,
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = message,
    )

    _log_results('on_delivery_nearby', results, order.order_id)
    return results


def on_delivery_completed(order: DeliveryOrder) -> dict:
    """Triggered when the rider marks the delivery as complete."""
    logger.info(f"[Scott] Delivery completed trigger | order={order.order_id}")

    title   = "Delivery Completed"
    message = (
        f"Your delivery has been completed successfully!\n"
        f"Item: {order.item_description}\n"
        f"Delivered to: {order.delivery_address}\n"
        f"Tracking reference: {order.tracking_code}\n\n"
        f"Thank you for using Scott Delivery."
    )

    results = {}

    results['email'] = _client.send_email(
        user_id = order.user_email,
        title   = title,
        message = message,
    )
    results['sms'] = _client.send_sms(
        user_id = order.user_phone,
        title   = title,
        message = (
            f"Delivered! {order.item_description} has arrived at "
            f"{order.delivery_address}. Ref: {order.tracking_code}"
        ),
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"Your package has been delivered. Tap to rate your experience.",
    )

    _log_results('on_delivery_completed', results, order.order_id)
    return results


def on_delivery_failed(order: DeliveryOrder, reason: str) -> dict:
    """Triggered when delivery attempt fails."""
    logger.info(f"[Scott] Failed delivery trigger | order={order.order_id}")

    title   = "Delivery Attempt Failed"
    message = (
        f"We were unable to complete your delivery.\n"
        f"Reason: {reason}\n"
        f"Our team will attempt re-delivery within 24 hours. "
        f"Tracking: {order.tracking_code}"
    )

    results = {}

    results['sms'] = _client.send_sms(
        user_id = order.user_phone,
        title   = title,
        message = message,
    )
    results['in_app'] = _client.send_in_app(
        user_id = order.user_id,
        title   = title,
        message = f"Delivery failed: {reason}. Re-attempt within 24 hours.",
    )

    _log_results('on_delivery_failed', results, order.order_id)
    return results


def _log_results(trigger: str, results: dict, reference: str):
    for channel, result in results.items():
        if result.success:
            logger.info(
                f"[Scott:{trigger}] {channel} queued | "
                f"ref={reference} | id={result.notification_id}"
            )
        else:
            logger.error(
                f"[Scott:{trigger}] {channel} FAILED | "
                f"ref={reference} | error={result.error}"
            )