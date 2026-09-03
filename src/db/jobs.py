"""Job listing database operations."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .client import get_supabase_client

logger = logging.getLogger(__name__)


def add_job_listing(
    channel: str,
    message_id: int,
    message_link: str,
    summary: str,
    raw_text: str = "",
) -> bool:
    """Insert a new scraped job listing into Supabase."""
    try:
        supabase = get_supabase_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "channel": channel,
            "message_id": message_id,
            "message_link": message_link,
            "summary": summary,
        }
        # Include optional fields if table supports them
        try:
            payload["raw_text"] = raw_text
            payload["scraped_at"] = now_iso
            response = supabase.table("job_listings").insert(payload).execute()
            if response.data:
                logger.debug(f"Inserted job {channel}:{message_id}")
                return True
        except Exception:
            # Fallback to minimal schema
            minimal_payload = {
                "channel": channel,
                "message_id": message_id,
                "message_link": message_link,
                "summary": summary,
            }
            response = supabase.table("job_listings").insert(minimal_payload).execute()
            return bool(response.data)
        return True
    except Exception as e:
        logger.error(f"Error adding job listing ({channel}:{message_id}): {e}")
        return False


def get_all_job_listings() -> List[Dict[str, Any]]:
    """Retrieve all current job listings."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("job_listings").select("*").execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching job listings: {e}")
        return []


def clear_job_listings() -> bool:
    """Clear all processed job listings."""
    try:
        supabase = get_supabase_client()
        supabase.table("job_listings").delete().neq("id", 0).execute()
        logger.info("Cleared job listings from database")
        return True
    except Exception as e:
        logger.error(f"Error clearing job listings: {e}")
        return False
