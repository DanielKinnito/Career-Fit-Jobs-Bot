import pytest
from unittest.mock import MagicMock, patch
from src.db.profiles import (
    validate_cv_file,
    upsert_user_profile,
    get_user_profile,
)


def test_validate_cv_file_allowed_extensions():
    """PDF, DOCX, and DOC must be valid, others rejected."""
    is_valid, err = validate_cv_file("resume.pdf", 1024 * 100)
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_cv_file("my_cv.docx", 1024 * 100)
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_cv_file("my_cv.doc", 1024 * 100)
    assert is_valid is True
    assert err == ""

    is_valid, err = validate_cv_file("malicious.exe", 1024 * 100)
    assert is_valid is False
    assert "extension" in err.lower()

    is_valid, err = validate_cv_file("image.png", 1024 * 100)
    assert is_valid is False


def test_validate_cv_file_size_limit():
    """Files exceeding 10MB must be rejected."""
    max_bytes = 10 * 1024 * 1024
    is_valid, err = validate_cv_file("resume.pdf", max_bytes)
    assert is_valid is True

    is_valid, err = validate_cv_file("huge_file.pdf", max_bytes + 1)
    assert is_valid is False
    assert "size" in err.lower()


def test_upsert_user_profile_mocked():
    """Profile upsert formats payload and executes through Supabase."""
    mock_client = MagicMock()
    # Mock get_user_by_telegram_id
    mock_client.table().select().eq().execute.return_value.data = [{"id": 42, "telegram_id": 99999}]
    # Mock user_profiles upsert
    mock_client.table().upsert().execute.return_value.data = [{"id": 1, "user_id": 42, "skills": "Python"}]

    with patch("src.db.profiles.get_supabase_client", return_value=mock_client), \
         patch("src.db.profiles.get_user_by_telegram_id", return_value={"id": 42, "telegram_id": 99999}):
        success = upsert_user_profile(
            telegram_id=99999,
            skills="Python, FastAPI, SQL",
            experience="3 years backend engineering",
        )
        assert success is True


def test_get_user_profile_found_mocked():
    """Profile retrieval joins user record and returns fields."""
    mock_client = MagicMock()
    mock_client.table().select().eq().execute.return_value.data = [{
        "id": 10,
        "user_id": 42,
        "cv_storage_path": "cvs/99999_resume.pdf",
        "cv_original_filename": "resume.pdf",
        "skills": "Python, React",
        "experience": "5 years",
        "created_at": "2026-09-03T12:00:00Z",
        "updated_at": "2026-09-03T12:00:00Z",
    }]

    with patch("src.db.profiles.get_supabase_client", return_value=mock_client), \
         patch("src.db.profiles.get_user_by_telegram_id", return_value={"id": 42, "telegram_id": 99999}):
        profile = get_user_profile(telegram_id=99999)
        assert profile is not None
        assert profile["cv_original_filename"] == "resume.pdf"
        assert profile["skills"] == "Python, React"
