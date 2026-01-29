#!/usr/bin/env python3
"""
Example: Using the scheduler to send scheduled Signal messages.

Install dependencies:
    pip install replyfast[scheduler]
    # or: pip install replyfast croniter
"""

from replyfast import SignalClient, Scheduler

DATA_DIR = "./data"


def main():
    # Create client and scheduler
    client = SignalClient(DATA_DIR)
    scheduler = Scheduler()

    if not client.is_registered_sync():
        print("Not registered! Run register.py first.")
        return

    info = client.whoami_sync()
    print(f"Logged in as: {info.phone_number}")

    # Example 1: Send a message every day at 9:00 AM
    def send_daily_greeting():
        contact = client.find_contact_by_phone_sync("+1234567890")
        if contact:
            client.send_message_sync(contact.uuid, "Good morning! Have a great day!")
            print(f"Sent morning greeting to {contact.name}")

    scheduler.register(
        "0 9 * * *",  # 9:00 AM every day
        send_daily_greeting,
        name="morning-greeting"
    )

    # Example 2: Send weekly report every Monday at 10:00 AM
    def send_weekly_report(recipient_uuid, report_type):
        message = f"Weekly {report_type} report is ready!"
        client.send_message_sync(recipient_uuid, message)
        print(f"Sent weekly report")

    scheduler.register(
        "0 10 * * 1",  # 10:00 AM every Monday
        send_weekly_report,
        args=("recipient-uuid-here", "status"),
        name="weekly-report"
    )

    # Example 3: Send reminder every hour during work hours (9 AM - 5 PM on weekdays)
    def hourly_reminder():
        print("Hourly check...")
        # Add your logic here

    scheduler.register(
        "0 9-17 * * 1-5",  # Every hour from 9-17 on Mon-Fri
        hourly_reminder,
        name="work-hours-check"
    )

    # Example 4: Using a lambda for simple tasks
    scheduler.register(
        "*/30 * * * *",  # Every 30 minutes
        lambda: print("30-minute heartbeat"),
        name="heartbeat"
    )

    # List all scheduled jobs
    print("\nScheduled jobs:")
    for job in scheduler.list_jobs():
        print(f"  - {job.name}: {job.cron_expr} (next: {job.next_run})")

    # Run the scheduler
    print("\nStarting scheduler... (Ctrl+C to stop)")
    scheduler.run()


# Alternative: Using the decorator syntax
def decorator_example():
    from replyfast import schedule, get_scheduler, SignalClient

    client = SignalClient("./data")

    @schedule("0 9 * * *", name="morning-message")
    def morning_task():
        # This function will run every day at 9 AM
        contact = client.find_contact_by_phone_sync("+1234567890")
        if contact:
            client.send_message_sync(contact.uuid, "Good morning!")

    @schedule("*/5 * * * *", name="every-5-min")
    def frequent_task():
        print("Running every 5 minutes")

    # Start the scheduler
    get_scheduler().run()


# Alternative: Running scheduler in background while also receiving messages
def background_scheduler_example():
    from replyfast import SignalClient, Scheduler

    client = SignalClient("./data")
    scheduler = Scheduler()

    # Register some scheduled tasks
    scheduler.register(
        "0 * * * *",  # Every hour
        lambda: print("Hourly task"),
        name="hourly"
    )

    # Start scheduler in background
    scheduler.start()

    # Now receive messages (this blocks)
    def on_message(msg):
        if msg.is_queue_empty:
            print("Ready to receive messages")
            return True
        if msg.body:
            print(f"Received: {msg.body}")
            # Auto-reply example
            if msg.body.lower() == "ping":
                client.send_message_sync(msg.sender, "pong!")
        return True

    try:
        client.receive_messages_sync(on_message)
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()
