"""
ReplyFast - Signal messaging library using Presage

A Python library for interacting with Signal messenger using the Presage Rust crate.

Example usage:
    from replyfast import SignalClient

    # Create client
    client = SignalClient("./data")

    # Link as secondary device (will print QR code URL)
    def on_url(url):
        print(f"Scan this QR code: {url}")
    client.link_device_sync("MyDevice", on_url)

    # Send a message
    client.send_message_sync("recipient-uuid", "Hello!")

    # Receive messages with callback
    def on_message(msg):
        if msg.is_queue_empty:
            print("Initial sync complete")
            return True
        print(f"From: {msg.sender}, Body: {msg.body}")
        return True  # Return True to continue, False to stop

    client.receive_messages_sync(on_message)
"""

from replyfast._replyfast import (
    SignalClient,
    Message,
    Contact,
    Group,
    AccountInfo,
)
from replyfast.scheduler import Scheduler, ScheduledJob, schedule, get_scheduler

__all__ = [
    "SignalClient",
    "Message",
    "Contact",
    "Group",
    "AccountInfo",
    "Scheduler",
    "ScheduledJob",
    "schedule",
    "get_scheduler",
]

__version__ = "0.1.0"
