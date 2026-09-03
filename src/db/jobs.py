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
            "raw_text": raw_text,
            "scraped_at": now_iso,
        }
        response = supabase.table("job_listings").insert(payload).execute()
        if response.data:
            logger.debug(f"Inserted job {channel}:{message_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error adding job listing ({channel}:{message_id}): {e}")
        return False


def get_all_job_listings(limit: int = 200) -> List[Dict[str, Any]]:
    """Retrieve recent job listings up to limit."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("job_listings")
            .select("*")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching job listings: {e}")
        return []


def get_unnotified_job_listings(min_job_id: int = 0, limit: int = 500) -> List[Dict[str, Any]]:
    """Retrieve job listings with ID strictly greater than min_job_id."""
    try:
        supabase = get_supabase_client()
        query = (
            supabase.table("job_listings")
            .select("*")
            .order("id", desc=False)
            .limit(limit)
        )
        if min_job_id > 0:
            query = query.gt("id", min_job_id)
        response = query.execute()
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching unnotified job listings: {e}")
        return []


def get_recent_job_listings(limit: int = 60) -> List[Dict[str, Any]]:
    """Retrieve recent job listings ordered from newest to oldest."""
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("job_listings")
            .select("id, channel, message_id, message_link, summary, raw_text, scraped_at")
            .order("id", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []
    except Exception as e:
        logger.error(f"Error fetching recent jobs: {e}")
        return []


def get_matched_jobs_for_user(preferences: List[str], limit: int = 40) -> List[Dict[str, Any]]:
    """Retrieve recent job listings that match any of the given preferences."""
    if not preferences:
        return []

    recent = get_recent_job_listings(limit=150)
    matched = []
    seen_ids = set()

    for job in recent:
        if job.get("id") in seen_ids:
            continue
        content = (job.get("summary", "") + " " + (job.get("raw_text") or "")).lower()
        for pref in preferences:
            if pref.lower() in content:
                matched.append(job)
                seen_ids.add(job.get("id"))
                break
        if len(matched) >= limit:
            break

    return matched


def clear_job_listings() -> bool:
    """Clear processed job listings (deprecated, retained for backwards compatibility)."""
    try:
        supabase = get_supabase_client()
        supabase.table("job_listings").delete().neq("id", 0).execute()
        logger.info("Cleared job listings from database")
        return True
    except Exception as e:
        logger.error(f"Error clearing job listings: {e}")
        return False
