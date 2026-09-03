"""Helper script to generate a Telethon StringSession for headless CI/CD runs."""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE_NUMBER


async def main():
    print("=" * 60)
    print("TELETHON STRINGSESSION GENERATOR")
    print("=" * 60)
    print("Generates an in-memory session string for GitHub Actions.")
    print("Your session will NOT be saved to a file.\n")

    default_api_id = str(TELEGRAM_API_ID) if TELEGRAM_API_ID else ""
    api_id_input = input(f"Enter TELEGRAM_API_ID [{default_api_id}]: ").strip() or default_api_id

    default_hash = TELEGRAM_API_HASH or ""
    api_hash = input(f"Enter TELEGRAM_API_HASH [{default_hash}]: ").strip() or default_hash

    default_phone = TELEGRAM_PHONE_NUMBER or ""
    print("Note: For Ethiopian numbers, use +251 followed by 9 digits (no leading 0), e.g. +251777463046")
    phone = input(f"Enter your phone number (international format) [{default_phone}]: ").strip() or default_phone

    if not api_id_input or not api_hash or not phone:
        print("Error: API ID, API Hash, and Phone are all required.")
        return

    api_id = int(api_id_input)

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start(phone=phone)

    session_string = client.session.save()
    print("\n" + "=" * 60)
    print("SUCCESS! Here is your TELETHON_SESSION_STRING:")
    print("=" * 60)
    print(session_string)
    print("=" * 60)
    print("\nCopy this string and add it to:")
    print("1. Your local .env file (TELETHON_SESSION_STRING=...)")
    print("2. GitHub repository secrets (TELETHON_SESSION_STRING)")
    print("Never share or commit this string publicly.\n")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
