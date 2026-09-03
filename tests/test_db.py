from unittest.mock import MagicMock
import pytest
from src.db.users import get_or_create_user, get_user_preferences
from src.db.scraper_state import get_channel_watermark, update_channel_watermark
from src.db.jobs import add_job_listing, clear_job_listings


def test_get_user_preferences_found(monkeypatch):
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table

    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    # Return simulated user data
    mock_response = MagicMock()
    mock_response.data = [{"telegram_id": 99999, "preferences": ["Developer", "Data Science"]}]
    mock_eq.execute.return_value = mock_response

    monkeypatch.setattr("src.db.users.get_supabase_client", lambda: mock_supabase)

    prefs = get_user_preferences(99999)
    assert prefs == ["Developer", "Data Science"]


def test_get_channel_watermark(monkeypatch):
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table

    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    mock_response = MagicMock()
    mock_response.data = [{"last_message_id": 450}]
    mock_eq.execute.return_value = mock_response

    monkeypatch.setattr("src.db.scraper_state.get_supabase_client", lambda: mock_supabase)

    watermark = get_channel_watermark("@Maroset")
    assert watermark == 450


def test_update_channel_watermark(monkeypatch):
    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_upsert = MagicMock()
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute.return_value = MagicMock()

    monkeypatch.setattr("src.db.scraper_state.get_supabase_client", lambda: mock_supabase)

    success = update_channel_watermark("@Maroset", 500)
    assert success is True
    mock_table.upsert.assert_called_once()
