#!/usr/bin/env python3
"""Signal Registration Script for ReplyFast

This script guides you through linking ReplyFast as a secondary device
to your existing Signal account.
"""

import sys

from replyfast import SignalClient

DATA_DIR = "./data"


def main():
    print("=== ReplyFast Signal Registration ===\n")

    client = SignalClient(DATA_DIR)

    # Check if already registered
    if client.is_registered_sync():
        print("Already registered!")
        info = client.whoami_sync()
        print(f"Phone: {info.phone_number}")
        print(f"UUID: {info.uuid}")
        print(f"Device ID: {info.device_id}")
        return

    link_device(client)


def link_device(client):
    print("--- Secondary Device Linking ---")
    print("\nThis will link ReplyFast as a secondary device to your Signal account.")
    print("You will need your phone with Signal installed.\n")

    device_name = input("Device name (default: ReplyFast): ").strip() or "ReplyFast"

    print("\nGenerating linking URL...")
    print("Open Signal app -> Settings -> Linked Devices -> Link New Device")
    print()

    def on_url(url):
        print(f"\nProvisioning URL: {url}")
        print()

        # Generate ASCII QR code if qrcode is available
        try:
            import qrcode

            qr = qrcode.QRCode()
            qr.add_data(url)
            qr.make()
            qr.print_ascii(invert=True)
        except ImportError:
            print("(Install 'qrcode' package for QR code display: pip install qrcode)")

        print("\nWaiting for you to scan the QR code with Signal...")

    try:
        client.link_device_sync(device_name, on_url)
        print("\nDevice linked successfully!")
        print("You can now use ReplyFast to send and receive messages.")
    except Exception as e:
        print(f"\nLinking failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
