"""User profile management and CV cloud storage operations."""

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from .client import get_supabase_client
from .users import get_user_by_telegram_id, get_or_create_user

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
RESUMES_BUCKET = "resumes"


def validate_cv_file(filename: str, size_bytes: int) -> Tuple[bool, str]:
    """Validate CV file format and size limits."""
    if not filename:
        return False, "Filename cannot be empty."

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"Unsupported file extension '{ext}'. Allowed formats: {allowed_str}"

    if size_bytes > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"File size exceeds maximum limit of {max_mb} MB."

    return True, ""


def get_user_profile(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full user profile including CV details, skills, and experience."""
    try:
        user = get_user_by_telegram_id(telegram_id)
        if not user or "id" not in user:
            return None

        supabase = get_supabase_client()
        response = (
            supabase.table("user_profiles")
            .select("*")
            .eq("user_id", user["id"])
            .execute()
        )

        if response.data and len(response.data) > 0:
            profile = response.data[0]
            profile["telegram_id"] = telegram_id
            return profile

        # Return default empty profile if none created yet
        return {
            "user_id": user["id"],
            "telegram_id": telegram_id,
            "cv_storage_path": None,
            "cv_original_filename": None,
            "skills": "",
            "experience": "",
            "created_at": None,
            "updated_at": None,
        }
    except Exception as e:
        logger.error(f"Error fetching profile for user {telegram_id}: {e}")
        return None


def upsert_user_profile(
    telegram_id: int,
    skills: Optional[str] = None,
    experience: Optional[str] = None,
    cv_storage_path: Optional[str] = None,
    cv_filename: Optional[str] = None,
) -> bool:
    """Insert or update user profile details."""
    try:
        user = get_or_create_user(telegram_id)
        user_id = user.get("id")
        if not user_id:
            logger.error(f"Cannot upsert profile: user {telegram_id} has no database id.")
            return False

        supabase = get_supabase_client()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Fetch existing profile if any
        existing_profile = get_user_profile(telegram_id) or {}

        payload: Dict[str, Any] = {
            "user_id": user_id,
            "updated_at": now_iso,
        }

        if skills is not None:
            payload["skills"] = skills.strip()
        elif "skills" in existing_profile and existing_profile["skills"]:
            payload["skills"] = existing_profile["skills"]

        if experience is not None:
            payload["experience"] = experience.strip()
        elif "experience" in existing_profile and existing_profile["experience"]:
            payload["experience"] = existing_profile["experience"]

        if cv_storage_path is not None:
            payload["cv_storage_path"] = cv_storage_path
        elif "cv_storage_path" in existing_profile and existing_profile["cv_storage_path"]:
            payload["cv_storage_path"] = existing_profile["cv_storage_path"]

        if cv_filename is not None:
            payload["cv_original_filename"] = cv_filename
        elif "cv_original_filename" in existing_profile and existing_profile["cv_original_filename"]:
            payload["cv_original_filename"] = existing_profile["cv_original_filename"]

        response = (
            supabase.table("user_profiles")
            .upsert(payload, on_conflict="user_id")
            .execute()
        )
        if response.data:
            logger.info(f"Updated profile for user {telegram_id} (user_id {user_id})")
            return True
        return False
    except Exception as e:
        logger.error(f"Error upserting profile for user {telegram_id}: {e}")
        return False


def upload_user_cv(
    telegram_id: int,
    filename: str,
    file_bytes: bytes,
) -> Optional[str]:
    """Upload a CV document to Supabase Storage and link it to user's profile."""
    is_valid, err = validate_cv_file(filename, len(file_bytes))
    if not is_valid:
        logger.warning(f"CV validation failed for user {telegram_id}: {err}")
        return None

    try:
        supabase = get_supabase_client()

        # Sanitize filename
        clean_name = re.sub(r"[^\w\.-]", "_", filename)
        storage_path = f"cvs/{telegram_id}_{clean_name}"

        # Determine content type
        ext = Path(clean_name).suffix.lower()
        content_type = "application/pdf" if ext == ".pdf" else "application/octet-stream"

        # Upload to Supabase Storage with overwrite enabled (CV swap capability)
        supabase.storage.from_(RESUMES_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        logger.info(f"Uploaded CV for user {telegram_id} to {storage_path}")

        # Update user profile record
        upsert_user_profile(
            telegram_id=telegram_id,
            cv_storage_path=storage_path,
            cv_filename=filename,
        )

        return storage_path
    except Exception as e:
        logger.error(f"Failed to upload CV to Supabase Storage for user {telegram_id}: {e}")
        return None


def get_user_cv_signed_url(storage_path: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a temporary signed download URL for an uploaded CV."""
    if not storage_path:
        return None

    try:
        supabase = get_supabase_client()
        res = supabase.storage.from_(RESUMES_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=expires_in,
        )
        if isinstance(res, dict) and "signedURL" in res:
            return res["signedURL"]
        return str(res)
    except Exception as e:
        logger.error(f"Error creating signed URL for {storage_path}: {e}")
        return None
