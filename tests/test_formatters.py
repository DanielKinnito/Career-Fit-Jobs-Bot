import pytest
from src.bot.formatters import escape_markdown_v2, format_summary_message


def test_escape_markdown_v2():
    raw_text = "Hello! [Job] Developer (Senior) - $100* & 50% / test."
    escaped = escape_markdown_v2(raw_text)
    assert r"\!" in escaped
    assert r"\[" in escaped
    assert r"\]" in escaped
    assert r"\(" in escaped
    assert r"\)" in escaped
    assert r"\*" in escaped
    assert r"\-" in escaped
    assert r"\." in escaped


def test_format_summary_message():
    matched = {
        "Developer": [
            {"channel": "@Maroset", "summary": "Full stack developer needed"},
            {"channel": "@freelance_ethio", "summary": "Python dev vacancy"},
        ],
        "Design": [
            {"channel": "@Maroset", "summary": "UI/UX Designer role"},
        ],
    }
    summary = format_summary_message(matched)
    assert "Latest Job Matches" in summary
    assert "Developer: 2 job(s)" in summary
    assert "@Maroset" in summary
    assert "@freelance_ethio" in summary
    assert "Design: 1 job(s)" in summary
