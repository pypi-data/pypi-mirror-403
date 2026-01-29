# ReplyFast

Signal messaging library for Python using [Presage](https://github.com/whisperfish/presage) (Rust).

## Installation

```bash
uv pip install replyfast
```

## Quick Start

```python
from replyfast import SignalClient

# Create client
client = SignalClient("./data")

# Link as secondary device (first time only)
def on_url(url):
    print(f"Scan this QR code with Signal app: {url}")

client.link_device_sync("MyDevice", on_url)

# Send a message
client.send_message_sync("recipient-uuid", "Hello!")

# Or find contact by phone/name first
contact = client.find_contact_by_phone_sync("+1234567890")
if contact:
    client.send_message_sync(contact.uuid, "Hello!")

# Receive messages
def on_message(msg):
    if msg.is_queue_empty:
        print("Initial sync complete")
        return True

    print(f"From: {msg.sender}, Body: {msg.body}")
    return True  # Return True to continue, False to stop

client.receive_messages_sync(on_message)
```

## API Reference

### SignalClient

| Method | Description |
|--------|-------------|
| `is_registered_sync()` | Check if device is linked |
| `link_device_sync(name, callback)` | Link as secondary device |
| `send_message_sync(uuid, message)` | Send message to contact |
| `send_group_message_sync(group_id, message)` | Send message to group |
| `receive_messages_sync(callback)` | Receive messages with callback |
| `get_contacts_sync()` | List synced contacts |
| `get_groups_sync()` | List groups |
| `find_contact_by_phone_sync(phone)` | Find contact by phone number |
| `find_contacts_by_name_sync(name)` | Find contacts by name |
| `whoami_sync()` | Get account info |

### Message

| Field | Type | Description |
|-------|------|-------------|
| `sender` | `str` | Sender's UUID |
| `body` | `str \| None` | Message text |
| `timestamp` | `int` | Unix timestamp (ms) |
| `group_id` | `str \| None` | Group ID if group message |
| `is_read_receipt` | `bool` | Is read receipt |
| `is_typing_indicator` | `bool` | Is typing indicator |
| `is_queue_empty` | `bool` | Initial sync complete marker |

## Scheduler

Send messages at scheduled times using cron syntax:

```python
from replyfast import SignalClient, Scheduler

client = SignalClient("./data")
scheduler = Scheduler()

# Send daily greeting at 9:00 AM
def send_greeting():
    contact = client.find_contact_by_phone_sync("+1234567890")
    if contact:
        client.send_message_sync(contact.uuid, "Good morning!")

scheduler.register(
    "0 9 * * *",  # cron: minute hour day month weekday
    send_greeting,
    name="morning-greeting"
)

# With arguments
scheduler.register(
    "0 10 * * 1",  # Every Monday at 10 AM
    client.send_message_sync,
    args=("uuid-here", "Weekly reminder!"),
    name="weekly-reminder"
)

# Run scheduler (blocking)
scheduler.run()

# Or run in background
scheduler.start()
# ... do other things ...
scheduler.stop()
```

### Cron Expression Format

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, 0=Sunday)
│ │ │ │ │
* * * * *
```

Examples:
- `*/5 * * * *` - Every 5 minutes
- `0 9 * * *` - Every day at 9:00 AM
- `0 9 * * 1-5` - Weekdays at 9:00 AM
- `30 */2 * * *` - Every 2 hours at minute 30

### Decorator Syntax

```python
from replyfast import schedule, get_scheduler

@schedule("0 9 * * *")
def daily_task():
    print("Runs every day at 9 AM")

get_scheduler().start()
```

## Installation

```bash
uv pip install replyfast

# With optional dependencies
uv pip install replyfast[scheduler]  # For cron scheduling
uv pip install replyfast[qrcode]     # For QR code display
uv pip install replyfast[all]        # Everything
```

## Requirements

- Python 3.10+
- Rust toolchain (for building from source)

## License

BSD-2-Clause
