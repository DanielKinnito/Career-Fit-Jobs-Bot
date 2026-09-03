"""User management database operations."""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from .client import get_supabase_client

logger = logging.getLogger(__name__)


def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user record by Telegram ID."""
    try:
        supabase = get_supabase_client()
        # Support both telegram_id (new schema) and user_id (legacy schema)
        try:
            response = supabase.table("users").select("*").eq("telegram_id", telegram_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception:
            # Fallback to legacy column name if migration not yet applied
            response = supabase.table("users").select("*").eq("user_id", telegram_id).execute()
            if response.data and len(response.data) > 0:
                user = response.data[0]
                user["telegram_id"] = user.get("user_id")
                return user
        return None
    except Exception as e:
        logger.error(f"Error fetching user by telegram_id {telegram_id}: {e}")
        return None


def get_or_create_user(telegram_id: int) -> Dict[str, Any]:
    """Ensure user exists in the database. Returns user record."""
    existing = get_user_by_telegram_id(telegram_id)
    if existing:
        return existing

    supabase = get_supabase_client()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        # Try new schema first
        payload = {
            "telegram_id": telegram_id,
            "preferences": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        response = supabase.table("users").insert(payload).execute()
        if response.data:
            logger.info(f"Created new user with telegram_id {telegram_id}")
            return response.data[0]
    except Exception as e:
        logger.warning(f"Could not insert with telegram_id, attempting legacy user_id: {e}")
        try:
            legacy_payload = {
                "user_id": telegram_id,
                "preferences": [],
                "created_at": now_iso,
            }
            response = supabase.table("users").insert(legacy_payload).execute()
            if response.data:
                user = response.data[0]
                user["telegram_id"] = telegram_id
                return user
        except Exception as legacy_err:
            logger.error(f"Failed to create user {telegram_id}: {legacy_err}")

    return {"telegram_id": telegram_id, "preferences": []}


def update_user_preferences(telegram_id: int, preferences: List[str]) -> bool:
    """Update job preference categories for a user."""
    try:
        supabase = get_supabase_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Try update using telegram_id
        try:
            response = (
                supabase.table("users")
                .update({"preferences": preferences, "updated_at": now_iso})
                .eq("telegram_id", telegram_id)
                .execute()
            )
            if response.data:
                logger.info(f"Updated preferences for user {telegram_id}")
                return True
        except Exception:
            pass

        # Fallback to legacy user_id column
        response = (
            supabase.table("users")
            .update({"preferences": preferences})
            .eq("user_id", telegram_id)
            .execute()
        )
        logger.info(f"Updated preferences (legacy) for user {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating preferences for user {telegram_id}: {e}")
        return False


def get_user_preferences(telegram_id: int) -> List[str]:
    """Retrieve selected preferences for a user."""
    user = get_user_by_telegram_id(telegram_id)
    if user and user.get("preferences") is not None:
        prefs = user["preferences"]
        if isinstance(prefs, list):
            return prefs
        return []
    return []


def get_all_active_users() -> List[Dict[str, Any]]:
    """Retrieve all users eligible to receive updates."""
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").execute()
        users = response.data or []
        # Normalize telegram_id
        for u in users:
            if "telegram_id" not in u and "user_id" in u:
                u["telegram_id"] = u["user_id"]
        return users
    except Exception as e:
        logger.error(f"Error fetching active users: {e}")
        return []
