#!/usr/bin/env python3
"""
Demo bot that sends system stats via Signal on a schedule.

Environment variables:
    DEMO_RECIPIENT: UUID of the recipient to send messages to
    SIGNAL_DATA_DIR: Path to Signal data directory (default: ./data)
"""

import logging
import os
import subprocess
import time

from replyfast import Scheduler, SignalClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
DATA_DIR = os.environ.get("SIGNAL_DATA_DIR", "./data")
DEMO_RECIPIENT = os.environ.get("DEMO_RECIPIENT")


def run_command(cmd: str) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return f"Command timed out: {cmd}"
    except Exception as e:
        return f"Error running command: {e}"


def send_disk_usage(client: SignalClient):
    """Send df -h output to DEMO_RECIPIENT."""
    if not DEMO_RECIPIENT:
        logger.warning("DEMO_RECIPIENT not set, skipping disk usage report")
        return

    try:
        output = run_command("df -h")
        message = f"[Disk Usage]\n```\n{output}```"
        client.send_message_sync(DEMO_RECIPIENT, message)
        logger.info("Sent disk usage report")
    except Exception as e:
        logger.error(f"Failed to send disk usage: {e}")


def send_memory_usage(client: SignalClient):
    """Send free -m output to DEMO_RECIPIENT."""
    if not DEMO_RECIPIENT:
        logger.warning("DEMO_RECIPIENT not set, skipping memory usage report")
        return

    try:
        output = run_command("free -m")
        message = f"[Memory Usage]\n```\n{output}```"
        client.send_message_sync(DEMO_RECIPIENT, message)
        logger.info("Sent memory usage report")
    except Exception as e:
        logger.error(f"Failed to send memory usage: {e}")


def setup_scheduled_jobs(scheduler: Scheduler, client: SignalClient):
    """Register all periodic scheduled jobs."""
    # Disk usage - every 5 minutes
    scheduler.register(
        "*/5 * * * *",
        send_disk_usage,
        args=(client,),
        name="disk-usage",
    )

    # Memory usage - every hour
    scheduler.register(
        "0 * * * *",
        send_memory_usage,
        args=(client,),
        name="memory-usage",
    )

    logger.info(f"Registered {len(scheduler.list_jobs())} scheduled job(s)")


def on_message(client: SignalClient, scheduler: Scheduler):
    """Create message handler callback for receive_messages_sync."""
    scheduler_started = False

    def callback(msg):
        nonlocal scheduler_started

        # Skip non-text messages
        if msg.is_read_receipt or msg.is_typing_indicator:
            return True

        # Initial sync complete - start scheduler
        if msg.is_queue_empty:
            logger.info("Initial sync complete, ready to receive messages")
            if not scheduler_started:
                scheduler.start()
                scheduler_started = True
            return True

        # Skip messages without body
        if not msg.body:
            return True

        logger.info(f"Received message from {msg.sender}: {msg.body}")

        # Simple command handling
        text = msg.body.strip().lower()
        if text == "ping":
            client.send_message_sync(msg.sender, "Pong")
        elif text == "df":
            output = run_command("df -h")
            client.send_message_sync(msg.sender, f"```\n{output}```")
        elif text == "free":
            output = run_command("free -m")
            client.send_message_sync(msg.sender, f"```\n{output}```")
        elif text == "help":
            client.send_message_sync(
                msg.sender,
                "Commands: ping, df, free, help\n"
                "Scheduled: df -h every 5 min, free -m every hour",
            )

        return True

    return callback


def main():
    if not DEMO_RECIPIENT:
        logger.error("DEMO_RECIPIENT environment variable not set!")
        logger.error("Usage: DEMO_RECIPIENT=<uuid> python demo_bot.py")
        return

    client = SignalClient(DATA_DIR)

    if not client.is_registered_sync():
        logger.error("Not registered! Run register.py first.")
        return

    info = client.whoami_sync()
    logger.info(f"Logged in as: {info.phone_number}")
    logger.info(f"Sending reports to: {DEMO_RECIPIENT}")

    # Set up scheduler
    scheduler = Scheduler()
    setup_scheduled_jobs(scheduler, client)

    logger.info("Starting message receiver...")

    # Reconnection loop
    reconnect_delay = 5
    max_reconnect_delay = 300

    while True:
        try:
            client.receive_messages_sync(on_message(client, scheduler))
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Connection error: {e}")
            logger.info(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

    scheduler.stop()
    print("\nStopped")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
