"""Stateless single-run notification dispatcher matching jobs to user preferences."""

import sys
import asyncio
import logging
from typing import Dict, List, Any
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from src.config import TELEGRAM_BOT_TOKEN, WEBHOOK_URL
from src.db.users import get_all_active_users, get_user_preferences
from src.db.jobs import get_unnotified_job_listings
from src.db.scraper_state import get_channel_watermark, update_channel_watermark
from src.bot.formatters import (
    format_summary_message,
    create_job_update_telegraph_page,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("notifier")

NOTIFIER_WATERMARK_KEY = "__notifier_watermark__"


def match_jobs_with_preferences(
    jobs: List[Dict[str, Any]], preferences: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """Match job listings against a list of category preferences (case-insensitive substring)."""
    matches: Dict[str, List[Dict[str, Any]]] = {}
    if not preferences:
        return matches

    for job in jobs:
        content = (job.get("summary", "") + " " + (job.get("raw_text") or "")).lower()
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
    """Compose message, build Telegraph link with Instant View, and send alert."""
    try:
        summary_text = format_summary_message(matched_jobs)
        telegraph_url = create_job_update_telegraph_page(matched_jobs)

        keyboard = []
        row = []
        if telegraph_url:
            row.append(InlineKeyboardButton("⚡ Open Instant View", url=telegraph_url))

        # Add Mini App button if configured
        if WEBHOOK_URL and "your-domain" not in WEBHOOK_URL:
            base_url = WEBHOOK_URL.replace("/api/webhook", "").replace("/webhook", "").rstrip("/")
            if base_url.startswith("https://"):
                row.append(InlineKeyboardButton("📱 Open in App", web_app=WebAppInfo(url=f"{base_url}/app")))

        if row:
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        await bot.send_message(
            chat_id=telegram_id,
            text=summary_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
            disable_web_page_preview=False,
        )
        logger.info(f"Dispatched job update to user {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send updates to user {telegram_id}: {e}")
        return False


async def run() -> int:
    """Execute a single notification run matching unnotified jobs against active users."""
    logger.info("Starting single-pass notification dispatcher")
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured.")
        return 0

    watermark_id = get_channel_watermark(NOTIFIER_WATERMARK_KEY)
    jobs = get_unnotified_job_listings(min_job_id=watermark_id, limit=300)
    if not jobs:
        logger.info(f"No unnotified job listings found (watermark job ID: {watermark_id}).")
        return 0

    logger.info(f"Loaded {len(jobs)} unnotified jobs since ID {watermark_id}")
    max_job_id = max(j["id"] for j in jobs)

    users = get_all_active_users()
    if not users:
        logger.info("No active users found to receive notifications.")
        update_channel_watermark(NOTIFIER_WATERMARK_KEY, max_job_id)
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
                await asyncio.sleep(0.5)

        logger.info(f"Dispatched updates to {sent_count} user(s).")
        # Update watermark so jobs stay in DB for on-demand queries and Mini App browsing
        update_channel_watermark(NOTIFIER_WATERMARK_KEY, max_job_id)
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
