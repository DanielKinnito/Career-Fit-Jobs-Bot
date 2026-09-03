"""Stateless single-run notification dispatcher matching jobs to user preferences."""

import sys
import asyncio
import logging
from typing import Dict, List, Any
from telegram import Bot
from src.config import TELEGRAM_BOT_TOKEN
from src.db.users import get_all_active_users, get_user_preferences
from src.db.jobs import get_all_job_listings, clear_job_listings
from src.bot.formatters import (
    format_summary_message,
    create_job_update_telegraph_page,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("notifier")


def match_jobs_with_preferences(
    jobs: List[Dict[str, Any]], preferences: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """Match job listings against a list of category preferences (case-insensitive substring)."""
    matches: Dict[str, List[Dict[str, Any]]] = {}
    if not preferences:
        return matches

    for job in jobs:
        content = (job.get("summary", "") + " " + job.get("raw_text", "")).lower()
        for pref in preferences:
            pref_clean = pref.strip()
            if pref_clean.lower() in content:
                if pref_clean not in matches:
                    matches[pref_clean] = []
                matches[pref_clean].append(job)

    return matches


async def send_updates_to_user(
    bot: Bot,
    telegram_id: int,
    matched_jobs: Dict[str, List[Dict[str, Any]]],
) -> bool:
    """Compose message, build Telegraph link, and send alert to a single user."""
    try:
        summary_text = format_summary_message(matched_jobs)
        telegraph_url = create_job_update_telegraph_page(matched_jobs)

        message = summary_text
        if telegraph_url:
            message += f"\n\nView full details: {telegraph_url}"

        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            disable_web_page_preview=False,
        )
        logger.info(f"Dispatched job update to user {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send update to user {telegram_id}: {e}")
        return False


async def run() -> int:
    """Execute a single notification pass for all active users."""
    logger.info("Starting single-pass notification dispatcher")
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is required to send notifications.")

    jobs = get_all_job_listings()
    if not jobs:
        logger.info("No job listings available in database to dispatch.")
        return 0

    users = get_all_active_users()
    if not users:
        logger.info("No active users found to receive notifications.")
        return 0

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    sent_count = 0

    try:
        for user in users:
            telegram_id = user.get("telegram_id")
            if not telegram_id:
                continue

            prefs = user.get("preferences") or get_user_preferences(telegram_id)
            if not prefs:
                continue

            matched = match_jobs_with_preferences(jobs, prefs)
            if matched:
                success = await send_updates_to_user(bot, telegram_id, matched)
                if success:
                    sent_count += 1
                # Respect Telegram rate limit (approx 30 msgs/sec globally, 1/sec per user)
                await asyncio.sleep(0.5)

        logger.info(f"Dispatched updates to {sent_count} user(s).")
        # Clear processed job listings so the next run only processes new arrivals
        clear_job_listings()
        return sent_count
    finally:
        await bot.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Notifier manually interrupted.")
    except Exception as exc:
        logger.error(f"Notifier encountered critical error: {exc}")
        sys.exit(1)
