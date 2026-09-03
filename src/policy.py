"""Privacy policy generation and hosting."""

import logging
from datetime import datetime
from telegraph import Telegraph

logger = logging.getLogger(__name__)

_cached_policy_url = ""


def get_privacy_policy_url() -> str:
    """Return a hosted Telegraph privacy policy URL, cached in memory."""
    global _cached_policy_url
    if _cached_policy_url:
        return _cached_policy_url

    content = f"""
<h3>Privacy Policy for Career Fit Job Bot</h3>
<p>Last updated: {datetime.now().strftime("%B %d, %Y")}</p>

<h4>1. Information Collected</h4>
<p>• Telegram User ID<br>• Job categories and preferences you select<br>• Application tracking links submitted by you</p>

<h4>2. How Information Is Used</h4>
<p>• Matching relevant job listings to your criteria<br>• Delivering scheduled updates via Telegram</p>

<h4>3. Data Security & Retention</h4>
<p>User preferences are stored securely in Supabase. We do not sell or transfer personal data to third parties.</p>

<h4>4. Managing Preferences</h4>
<p>You may adjust or clear your target job categories at any time using the /preferences command.</p>
"""

    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="CareerFitPolicy")
        response = telegraph.create_page(
            title="Career Fit Job Bot - Privacy Policy",
            html_content=content,
            author_name="Career Fit Jobs Bot",
        )
        _cached_policy_url = response.get("url", "https://telegra.ph/Privacy-Policy-Career-Fit-Job-Bot")
        return _cached_policy_url
    except Exception as e:
        logger.warning(f"Could not generate dynamic Telegraph policy page: {e}")
        return "https://telegra.ph/Privacy-Policy-Career-Fit-Job-Bot"


if __name__ == "__main__":
    print(get_privacy_policy_url())
