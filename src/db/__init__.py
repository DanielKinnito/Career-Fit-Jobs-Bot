"""Database package for Career Fit Jobs Bot."""

from .client import get_supabase_client
from .users import (
    get_or_create_user,
    get_user_by_telegram_id,
    update_user_preferences,
    get_user_preferences,
    get_all_active_users,
)
from .jobs import (
    add_job_listing,
    get_all_job_listings,
    get_recent_job_listings,
    get_matched_jobs_for_user,
    clear_job_listings,
)
from .scraper_state import (
    get_channel_watermark,
    update_channel_watermark,
)
from .profiles import (
    get_user_profile,
    upsert_user_profile,
    upload_user_cv,
    get_user_cv_signed_url,
)

__all__ = [
    "get_supabase_client",
    "get_or_create_user",
    "get_user_by_telegram_id",
    "update_user_preferences",
    "get_user_preferences",
    "get_all_active_users",
    "add_job_listing",
    "get_all_job_listings",
    "get_recent_job_listings",
    "get_matched_jobs_for_user",
    "clear_job_listings",
    "get_channel_watermark",
    "update_channel_watermark",
    "get_user_profile",
    "upsert_user_profile",
    "upload_user_cv",
    "get_user_cv_signed_url",
]
