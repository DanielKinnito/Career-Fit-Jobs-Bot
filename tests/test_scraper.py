import pytest
from src.scraper.runner import is_job_related, load_keywords


def test_load_keywords():
    keywords = load_keywords()
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "developer" in keywords
    assert "engineer" in keywords


def test_is_job_related():
    keywords = ["hiring", "developer", "vacancy", "internship"]
    assert is_job_related("We are hiring full-time staff", keywords) is True
    assert is_job_related("Looking for an experienced developer", keywords) is True
    assert is_job_related("Daily general news update", keywords) is False
    assert is_job_related("", keywords) is False
