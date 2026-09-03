"""Local development bot runner using polling mode.

Use this script ONLY for quick local interactive testing without needing
to configure a public webhook URL or tunnel.

Production uses api/webhook.py hosted on Vercel.
"""

import os
import sys
import logging
from pathlib import Path

# Ensure project root is always in sys.path regardless of execution directory
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from telegram.ext import Application
from src.config import TELEGRAM_BOT_TOKEN
from src.bot.handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dev_bot")


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        sys.exit(1)

    print("=" * 60)
    print("CAREER FIT JOBS BOT — LOCAL DEVELOPMENT RUNNER")
    print("=" * 60)
    print("Bot is starting in local polling mode...")
    print("Open Telegram, find your bot, and send /start or /preferences!")
    print("Press Ctrl+C to stop.")
    print("=" * 60 + "\n")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    register_handlers(application)
    application.run_polling()


if __name__ == "__main__":
    main()
