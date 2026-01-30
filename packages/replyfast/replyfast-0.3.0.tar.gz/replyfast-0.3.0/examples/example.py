#!/usr/bin/env python3
"""
Example usage of ReplyFast Signal messaging library.

Before running this, you need to link your device using register.py
"""

from replyfast import SignalClient

DATA_DIR = "./data"


def main():
    client = SignalClient(DATA_DIR)

    # Check if registered
    if not client.is_registered_sync():
        print("Not registered! Please run register.py first.")
        return

    # Get account info
    info = client.whoami_sync()
    print(f"Logged in as: {info.phone_number}")
    print(f"UUID: {info.uuid}")
    print(f"Device ID: {info.device_id}")
    print()

    # List contacts
    contacts = client.get_contacts_sync()
    print(f"Contacts ({len(contacts)}):")
    for contact in contacts[:5]:  # Show first 5
        print(f"  - {contact.name or 'Unknown'}: {contact.uuid}")
    print()

    # List groups
    groups = client.get_groups_sync()
    print(f"Groups ({len(groups)}):")
    for group in groups[:5]:  # Show first 5
        print(f"  - {group.title}: {len(group.members)} members")
    print()

    # Receive messages with callback
    print("Listening for messages... (Ctrl+C to stop)")

    def on_message(msg):
        if msg.is_queue_empty:
            print("[Initial sync complete, waiting for new messages...]")
            return True

        if msg.is_typing_indicator:
            print(f"[{msg.sender[:8]}... is typing]")
            return True

        if msg.is_read_receipt:
            return True  # Skip read receipts

        sender = msg.sender[:8] + "..."
        if msg.group_id:
            print(f"[Group] {sender}: {msg.body}")
        else:
            print(f"{sender}: {msg.body}")

        return True  # Continue receiving

    try:
        client.receive_messages_sync(on_message)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
