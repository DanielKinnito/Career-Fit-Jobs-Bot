import pytest
from src.notifier.runner import match_jobs_with_preferences


def test_match_jobs_empty_preferences():
    jobs = [{"summary": "Senior Python Developer at Tech Co", "raw_text": ""}]
    matches = match_jobs_with_preferences(jobs, [])
    assert matches == {}


def test_match_jobs_hit():
    jobs = [
        {
            "summary": "We are hiring a Senior Python Developer with 3+ years experience.",
            "raw_text": "Tech company in Addis is looking for a Developer.",
            "channel": "@Maroset",
        },
        {
            "summary": "Accountant position open at Bank of Abyssinia.",
            "raw_text": "Finance and accounting degree required.",
            "channel": "@freelance_ethio",
        },
    ]

    prefs = ["Developer", "Accountant"]
    matched = match_jobs_with_preferences(jobs, prefs)

    assert "Developer" in matched
    assert len(matched["Developer"]) == 1
    assert "Accountant" in matched
    assert len(matched["Accountant"]) == 1


def test_match_jobs_no_match():
    jobs = [
        {"summary": "Cook needed for restaurant in Bole", "raw_text": ""},
    ]
    prefs = ["Developer", "Cybersecurity"]
    matched = match_jobs_with_preferences(jobs, prefs)
    assert matched == {}


def test_match_jobs_case_insensitive():
    jobs = [
        {"summary": "junior frontend DEVELOPER needed", "raw_text": ""},
    ]
    prefs = ["Developer"]
    matched = match_jobs_with_preferences(jobs, prefs)
    assert "Developer" in matched
    assert len(matched["Developer"]) == 1
