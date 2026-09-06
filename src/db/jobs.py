"""Job listing database operations."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from src.config import JOB_RETENTION_DAYS
from .client import get_supabase_client

logger = logging.getLogger(__name__)


def add_job_listing(
    channel: str,
    message_id: int,
    message_link: str,
    summary: str,
    raw_text: str = "",
    work_type: str = "Unspecified",
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
            "work_type": work_type,
            "scraped_at": now_iso,
        }
        try:
            response = supabase.table("job_listings").insert(payload).execute()
            if response.data:
                logger.debug(f"Inserted job {channel}:{message_id} ({work_type})")
                return True
        except Exception:
            # Fallback if work_type column is not yet migrated in Supabase
            payload.pop("work_type", None)
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


def get_recent_job_listings(
    limit: int = 100,
    time_range: Optional[str] = None,
    work_type: Optional[str] = None,
    has_salary: Optional[bool] = None,
    sort: str = "newest",
) -> List[Dict[str, Any]]:
    """Retrieve recent job listings with optional time, modality, and salary filters."""
    try:
        supabase = get_supabase_client()
        is_desc = (sort != "oldest")
        query = supabase.table("job_listings").select("*").order("id", desc=is_desc)

        # Apply time range filter
        if time_range and time_range != "all":
            now = datetime.now(timezone.utc)
            cutoff = None
            if time_range == "today":
                cutoff = now - timedelta(hours=24)
            elif time_range == "week":
                cutoff = now - timedelta(days=7)
            elif time_range == "two_weeks":
                cutoff = now - timedelta(days=14)
            elif time_range == "month":
                cutoff = now - timedelta(days=30)

            if cutoff:
                query = query.gte("scraped_at", cutoff.isoformat())

        query = query.limit(limit)
        response = query.execute()
        jobs = response.data or []

        # Filter by work modality if requested
        if work_type and work_type.lower() != "all":
            target = work_type.lower()
            filtered = []
            for j in jobs:
                j_wt = (j.get("work_type") or "").lower()
                content = (j.get("summary", "") + " " + (j.get("raw_text") or "")).lower()
                if (target in j_wt) or \
                   (target == "remote" and ("remote" in content or "wfh" in content or "work from home" in content)) or \
                   (target == "hybrid" and "hybrid" in content) or \
                   (target in ["on-site", "onsite"] and ("on-site" in content or "onsite" in content or "addis ababa" in content)):
                    filtered.append(j)
            jobs = filtered

        # Filter by salary if requested
        if has_salary:
            salary_indicators = ["salary", "etb", "birr", "ደመወዝ", "remuneration", "compensation", "negotiable", "$"]
            filtered = []
            for j in jobs:
                content = (j.get("summary", "") + " " + (j.get("raw_text") or "")).lower()
                if any(ind in content for ind in salary_indicators):
                    filtered.append(j)
            jobs = filtered

        return jobs
    except Exception as e:
        logger.error(f"Error fetching recent jobs: {e}")
        return []


def get_matched_jobs_for_user(
    preferences: List[str],
    limit: int = 50,
    time_range: Optional[str] = None,
    work_type: Optional[str] = None,
    has_salary: Optional[bool] = None,
    sort: str = "newest",
) -> List[Dict[str, Any]]:
    """Retrieve job listings matching user preferences with optional filters."""
    if not preferences:
        return []

    recent = get_recent_job_listings(
        limit=300,
        time_range=time_range,
        work_type=work_type,
        has_salary=has_salary,
        sort=sort,
    )
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


def cleanup_expired_job_listings(retention_days: Optional[int] = None) -> int:
    """Delete job listings older than retention_days to preserve database storage limits."""
    if retention_days is None:
        retention_days = JOB_RETENTION_DAYS

    try:
        supabase = get_supabase_client()
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_iso = cutoff.isoformat()

        response = (
            supabase.table("job_listings")
            .delete()
            .lt("scraped_at", cutoff_iso)
            .execute()
        )
        deleted_count = len(response.data) if response.data else 0
        logger.info(f"Cleaned up {deleted_count} expired job listings older than {retention_days} days (cutoff: {cutoff_iso})")
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up expired job listings: {e}")
        return 0


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
