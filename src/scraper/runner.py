"""Stateless single-run job scraper for Telegram channels."""

import os
import sys
import asyncio
import logging
from typing import List
from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config import (
    API_ID,
    API_HASH,
    TELEGRAM_PHONE_NUMBER,
    TELETHON_SESSION_STRING,
    CHANNELS,
)
from src.db.jobs import add_job_listing
from src.db.scraper_state import get_channel_watermark, update_channel_watermark
from src.scraper.classifier import is_certified_job_post, extract_work_type

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scraper")


def load_keywords() -> List[str]:
    """Load matching keywords from package directory."""
    keywords_path = os.path.join(os.path.dirname(__file__), "keywords.txt")
    if not os.path.exists(keywords_path):
        return []
    with open(keywords_path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def is_job_related(text: str, keywords: List[str]) -> bool:
    """Check if post text contains job vacancy indicators."""
    if not text:
        return False
    if not keywords:
        return True
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def init_telethon_client() -> TelegramClient:
    """Initialize Telethon client from session string or local session file."""
    if not API_ID or not API_HASH:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be configured.")

    if TELETHON_SESSION_STRING:
        logger.info("Initializing Telethon client using in-memory StringSession")
        return TelegramClient(StringSession(TELETHON_SESSION_STRING), API_ID, API_HASH)

    logger.info("Initializing Telethon client using local file session")
    return TelegramClient("session", API_ID, API_HASH)


async def scrape_channel(
    client: TelegramClient, channel: str, keywords: List[str]
) -> int:
    """Scrape new messages from a single channel since the last watermark."""
    channel_clean = channel.lstrip("@")
    last_id = get_channel_watermark(channel)
    logger.info(f"Scraping channel {channel} (watermark message_id: {last_id})")

    new_count = 0
    max_scraped_id = last_id

    try:
        # iter_messages with min_id returns messages newer than last_id
        async for message in client.iter_messages(channel, limit=100, min_id=last_id):
            if message.id > max_scraped_id:
                max_scraped_id = message.id

            raw_text = message.text or message.message or ""
            if not raw_text.strip():
                continue

            if not is_certified_job_post(raw_text):
                continue

            summary = raw_text[:300].strip()
            message_link = f"https://t.me/{channel_clean}/{message.id}"
            work_type = extract_work_type(raw_text)

            success = add_job_listing(
                channel=channel,
                message_id=message.id,
                message_link=message_link,
                summary=summary,
                raw_text=raw_text,
                work_type=work_type,
            )
            if success:
                new_count += 1

        if max_scraped_id > last_id:
            update_channel_watermark(channel, max_scraped_id)

        logger.info(
            f"Finished {channel}: saved {new_count} new job listing(s), watermark updated to {max_scraped_id}"
        )
        return new_count

    except Exception as e:
        logger.error(f"Error scraping channel {channel}: {e}")
        return 0


async def run() -> int:
    """Execute a single scraping pass across all configured channels."""
    logger.info("Starting single-pass channel scraper")
    keywords = load_keywords()
    client = init_telethon_client()

    if TELETHON_SESSION_STRING:
        await client.start()
    else:
        await client.start(phone=TELEGRAM_PHONE_NUMBER)

    total_scraped = 0
    try:
        for channel in CHANNELS:
            count = await scrape_channel(client, channel, keywords)
            total_scraped += count
            # Polite delay between channel requests to avoid Telegram flood limits
            await asyncio.sleep(1)
        logger.info(f"Scraping complete. Total new listings added: {total_scraped}")
        return total_scraped
    finally:
        await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Scraper manually interrupted.")
    except Exception as exc:
        logger.error(f"Scraper encountered critical error: {exc}")
        sys.exit(1)
