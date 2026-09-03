"""Scraper watermark and state tracking in Supabase."""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional
from .client import get_supabase_client

logger = logging.getLogger(__name__)


def get_channel_watermark(channel: str) -> int:
    """Get the highest message_id scraped for a channel. Returns 0 if none recorded."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("scraper_state")
            .select("last_message_id")
            .eq("channel", channel)
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0].get("last_message_id", 0)
        return 0
    except Exception as e:
        logger.warning(f"Could not get scraper state for {channel}: {e}")
        return 0


def update_channel_watermark(channel: str, last_message_id: int) -> bool:
    """Upsert channel watermark with the latest message_id and timestamp."""
    try:
        supabase = get_supabase_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "channel": channel,
            "last_message_id": last_message_id,
            "last_scraped_at": now_iso,
        }
        supabase.table("scraper_state").upsert(payload).execute()
        logger.debug(f"Updated scraper state for {channel} to message {last_message_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating scraper state for {channel}: {e}")
        return False


def get_all_watermarks() -> Dict[str, int]:
    """Get latest message ID for all tracked channels."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("scraper_state").select("channel, last_message_id").execute()
        result = {}
        for row in (response.data or []):
            result[row["channel"]] = row["last_message_id"]
        return result
    except Exception as e:
        logger.error(f"Error fetching all watermarks: {e}")
        return {}
