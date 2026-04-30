"""
python integrations/simulate.py

Runs a full end-to-end simulation of both Tixora and Scott Delivery
sending notifications through Notiflow. Run this with the Django server
and worker both active to see the complete flow.
"""

import os
import sys
import django
import time
import logging

# Set up Django so we can use its logger config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'notiflow_backend.settings')
django.setup()

logging.basicConfig(
    level  = logging.INFO,
    format = '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    datefmt= '%H:%M:%S',
)

from integrations.tixora.notification_triggers import (
    TicketOrder, on_ticket_purchased, on_event_reminder, on_ticket_cancelled,
)
from integrations.scott.notification_triggers import (
    DeliveryOrder, on_order_placed, on_order_dispatched,
    on_delivery_nearby, on_delivery_completed,
)


def separator(title: str):
    print(f"\n{'═' * 60}")
    print(f"  {title}")
    print('═' * 60)


def print_results(results: dict):
    for channel, result in results.items():
        icon   = "✓" if result.success else "✗"
        detail = result.notification_id if result.success else result.error
        print(f"  {icon} {channel:<8} → {detail}")


def run_tixora_simulation():
    separator("TIXORA — Ticket Purchase Lifecycle")

    # Create a realistic order
    order = TicketOrder(
        order_id      = "TIX-2025-00891",
        user_id       = "tixora_user_42",
        user_email    = "your.email@gmail.com",    # ← replace with real email to test
        user_phone    = "+254712345678",
        event_name    = "Nairobi Jazz Night — Vol. 12",
        event_date    = "Saturday, 10 May 2025 at 7:00 PM",
        event_venue   = "Alliance Française, Nairobi",
        ticket_count  = 2,
        total_amount  = "KES 3,200",
    )

    print("\n1. Ticket purchased:")
    results = on_ticket_purchased(order)
    print_results(results)

    time.sleep(2)

    print("\n2. Event reminder (24h before):")
    results = on_event_reminder(order, hours_before=24)
    print_results(results)

    time.sleep(2)

    print("\n3. Ticket cancelled (refund scenario):")
    results = on_ticket_cancelled(order, reason="Event postponed by organiser.")
    print_results(results)


def run_scott_simulation():
    separator("SCOTT DELIVERY — Full Delivery Lifecycle")

    order = DeliveryOrder(
        order_id          = "SCT-2025-04471",
        user_id           = "scott_user_17",
        user_email        = "your.email@gmail.com",    # ← replace with real email
        user_phone        = "+254798765432",
        recipient_name    = "Amara Osei",
        delivery_address  = "Westlands, Nairobi, Kenya",
        item_description  = "Electronics Package (2kg)",
        tracking_code     = "SCT-TRK-44712",
        estimated_arrival = "Today by 3:00 PM",
    )

    print("\n1. Order placed:")
    results = on_order_placed(order)
    print_results(results)
    time.sleep(2)

    print("\n2. Package dispatched (rider: James M.):")
    results = on_order_dispatched(order, rider_name="James M.")
    print_results(results)
    time.sleep(2)

    print("\n3. Rider 2 stops away:")
    results = on_delivery_nearby(order, stops_away=2)
    print_results(results)
    time.sleep(2)

    print("\n4. Delivery completed:")
    results = on_delivery_completed(order)
    print_results(results)


def check_inbox():
    separator("IN-APP INBOX CHECK")
    from integrations.notiflow_client import NotiflowClient

    for app_id, user_id in [('tixora', 'tixora_user_42'), ('scott', 'scott_user_17')]:
        client = NotiflowClient(app_id=app_id)
        count  = client.get_unread_count(user_id)
        inbox  = client.get_inbox(user_id)
        total  = inbox.get('count', 0) if inbox else 0
        print(f"\n  {app_id:<10} user={user_id}")
        print(f"  Total in-app notifications : {total}")
        print(f"  Unread count               : {count}")


if __name__ == '__main__':
    print("\n🚀 Notiflow Integration Simulation")
    print("Make sure: (1) Django server is running  (2) Worker is running\n")

    run_tixora_simulation()
    run_scott_simulation()
    check_inbox()

    separator("SIMULATION COMPLETE")
    print("\nCheck:")
    print("  • Your email inbox — ticket confirmation + delivery summary")
    print("  • Terminal 2 (worker) — SMS simulation logs")
    print("  • http://127.0.0.1:8000/admin/ — all notifications + logs")
    print("  • http://127.0.0.1:8000/notifications/?app_id=tixora")
    print("  • http://127.0.0.1:8000/notifications/?app_id=scott\n")