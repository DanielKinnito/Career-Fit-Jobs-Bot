"""Configure Telegram Bot profile, commands menu, and native Mini App chat menu button."""

import os
import sys
import asyncio
import logging
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from telegram import Bot, BotCommand, MenuButtonWebApp, MenuButtonCommands, WebAppInfo
from src.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("setup_profile")


async def configure_bot():
    """Apply official commands, descriptions, and Mini App menu button to the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN must be configured.")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # 1. Set Official Bot Commands
    commands = [
        BotCommand("start", "Launch Career Fit dashboard & preferences"),
        BotCommand("jobs", "View latest matched job bulletin with Instant View"),
        BotCommand("profile", "View your profile, CV status & experience"),
        BotCommand("skills", "Update your skills (e.g. /skills Python, React)"),
        BotCommand("experience", "Update your experience (e.g. /experience 3 yrs...)"),
        BotCommand("preferences", "Update your target career sectors & categories"),
        BotCommand("help", "About Career Fit matching and alert schedules"),
    ]
    await bot.set_my_commands(commands)
    logger.info("Successfully updated bot command menu.")

    # 2. Set Bot Description (shown on empty chat screen before /start)
    description = (
        "Welcome to Career Fit Jobs Bot!\n\n"
        "We automatically monitor Ethiopia's top Telegram employment channels, match vacancies "
        "to your career preferences, and deliver curated Instant View bulletins 3 times daily.\n\n"
        "Tap Start below to set up your preferences or browse vacancies in our interactive Mini App."
    )
    try:
        await bot.set_my_description(description)
        logger.info("Successfully set bot description.")
    except Exception as e:
        logger.warning(f"Could not set description: {e}")

    # 3. Set Short Description (shown in profile bio and sharing preview)
    short_description = "Curated Telegram job matching with Instant View bulletins & interactive Mini App."
    try:
        await bot.set_my_short_description(short_description)
        logger.info("Successfully set bot short description.")
    except Exception as e:
        logger.warning(f"Could not set short description: {e}")

    # 4. Set Native Input Bar Menu Button
    # If a live HTTPS URL is configured for WEBHOOK_URL, point the menu button directly to the Mini App!
    web_app_url = None
    if WEBHOOK_URL and "your-domain" not in WEBHOOK_URL:
        base_url = WEBHOOK_URL.replace("/api/webhook", "").replace("/webhook", "").rstrip("/")
        if base_url.startswith("https://"):
            web_app_url = f"{base_url}/app"

    if web_app_url:
        menu_button = MenuButtonWebApp(text="Career Fit", web_app=WebAppInfo(url=web_app_url))
        await bot.set_chat_menu_button(menu_button=menu_button)
        logger.info(f"Set native Telegram chat menu button to Mini App: {web_app_url}")
    else:
        await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
        logger.info("Set native Telegram chat menu button to standard commands menu.")

    await bot.shutdown()
    logger.info("Bot configuration complete!")


if __name__ == "__main__":
    asyncio.run(configure_bot())
