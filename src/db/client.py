"""Supabase client factory with connection pooling and validation."""

import logging
from typing import Optional
from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY

logger = logging.getLogger(__name__)

_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Returns the singleton Supabase client using service role key or anon key."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    # Backend processes (scraper, notifier, bot server) need service role privileges
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
    if not SUPABASE_URL or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY / SUPABASE_SERVICE_ROLE_KEY must be configured in environment variables."
        )

    try:
        _supabase_client = create_client(SUPABASE_URL, key)
        logger.debug("Initialized Supabase client successfully")
        return _supabase_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise


def get_supabase_admin_client() -> Client:
    """Returns the singleton Supabase admin client using the service role key."""
    global _supabase_admin_client
    if _supabase_admin_client is not None:
        return _supabase_admin_client

    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
    if not SUPABASE_URL or not key:
        raise ValueError("SUPABASE_URL and service role key must be configured.")

    try:
        _supabase_admin_client = create_client(SUPABASE_URL, key)
        logger.debug("Initialized Supabase admin client successfully")
        return _supabase_admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        raise
