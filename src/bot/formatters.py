"""Message formatting and Telegraph page creation."""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any
from telegraph import Telegraph

logger = logging.getLogger(__name__)


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 reserved characters."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


def format_summary_message(matched_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Format human-readable summary of job matches for Telegram delivery."""
    summary_lines = ["Latest Job Matches\n"]
    for category, jobs in matched_jobs.items():
        channels = {job.get("channel", "") for job in jobs}
        channels_str = ", ".join(sorted(ch for ch in channels if ch))
        summary_lines.append(f"• {category}: {len(jobs)} job(s) from {channels_str}")
    return "\n".join(summary_lines).strip()


def create_job_update_telegraph_page(matched_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate a clean Telegraph page containing all matched job details."""
    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="CareerFitJobs")

        content = "<h3>Latest Career Fit Job Matches</h3>"
        total_jobs_added = 0
        max_total_jobs = 35

        for category, jobs in matched_jobs.items():
            if total_jobs_added >= max_total_jobs:
                break
            content += f"<h4>📌 {category}</h4>"
            # Cap at 10 jobs per category
            for job in jobs[:10]:
                if total_jobs_added >= max_total_jobs:
                    break
                summary_text = job.get("summary", "")
                title = summary_text.split("\n")[0][:120] if summary_text else "Job Opportunity"
                channel = job.get("channel", "")
                link = job.get("message_link", "")

                content += f"""
                <p>
                <strong>Source:</strong> {channel}<br>
                <strong>Summary:</strong> {title}<br>
                <a href="{link}">View original Telegram post</a>
                </p>
                <hr>
                """
                total_jobs_added += 1

        current_date = datetime.now().strftime("%Y-%m-%d")
        response = telegraph.create_page(
            title=f"Career Fit Jobs - {current_date}",
            html_content=content,
            author_name="Career Fit Jobs Bot",
            return_content=True,
        )
        return response.get("url", "")
    except Exception as e:
        logger.error(f"Error creating Telegraph page: {e}")
        return ""
