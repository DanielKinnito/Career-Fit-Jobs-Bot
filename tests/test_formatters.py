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
    assert "Career Fit Jobs Bulletin" in summary
    assert "Developer" in summary
    assert "@Maroset" in summary
    assert "@freelance_ethio" in summary
    assert "Design" in summary


def test_format_summary_message_empty():
    summary = format_summary_message({})
    assert "No new vacancies matched" in summary
