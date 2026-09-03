"""Message formatting and Telegraph Instant View bulletin creation."""

import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from telegraph import Telegraph

logger = logging.getLogger(__name__)


def escape_markdown_v2(text: str) -> str:
    """Escape Telegram MarkdownV2 reserved characters."""
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(special_chars)}])", r"\\\1", text)


def format_summary_message(matched_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Format an elegant curated bulletin message for Telegram delivery."""
    total_jobs = sum(len(jobs) for jobs in matched_jobs.values())
    date_str = datetime.now(timezone.utc).strftime("%b %d, %Y")

    if total_jobs == 0:
        return (
            "✨ *Career Fit Jobs Bulletin*\n\n"
            "No new vacancies matched your selected categories in this alert batch.\n"
            "We'll notify you on the next scheduled run, or update your /preferences anytime."
        )

    lines = [
        "✨ *Career Fit Jobs Bulletin*",
        f"📅 *{date_str}*\n",
        f"🎯 *Found {total_jobs} new matching vacancy(ies):*\n",
    ]

    for category, jobs in matched_jobs.items():
        channels = {job.get("channel", "") for job in jobs}
        channels_str = ", ".join(sorted(ch for ch in channels if ch))
        lines.append(f"• *{category}* ({len(jobs)}): {channels_str}")

    lines.append("\n⚡ *Tap Instant View below to read all curated listings in full.*")
    return "\n".join(lines).strip()


def create_job_update_telegraph_page(matched_jobs: Dict[str, List[Dict[str, Any]]]) -> str:
    """Generate a clean, magazine-style Telegraph page for Telegram Instant View."""
    try:
        telegraph = Telegraph()
        telegraph.create_account(short_name="CareerFitJobs")

        current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
        total_jobs = sum(len(jobs) for jobs in matched_jobs.values())

        content = f"""
        <p><strong>Curated Daily Job Digest</strong> • {current_date}</p>
        <p><em>Matched {total_jobs} vacancies across Ethiopia's top career channels. Tap any link to apply or view on Telegram.</em></p>
        <hr>
        """

        total_jobs_added = 0
        max_total_jobs = 40

        for category, jobs in matched_jobs.items():
            if total_jobs_added >= max_total_jobs:
                break

            content += f"<h3>📌 {category} ({len(jobs)})</h3>"

            for job in jobs[:10]:
                if total_jobs_added >= max_total_jobs:
                    break

                raw_summary = job.get("summary", "").strip()
                summary_lines = [line.strip() for line in raw_summary.split("\n") if line.strip()]
                title = summary_lines[0][:120] if summary_lines else f"{category} Position"
                body = " ".join(summary_lines[1:4])[:240] if len(summary_lines) > 1 else ""

                channel = job.get("channel", "Telegram Channel")
                link = job.get("message_link", "#")

                work_type = job.get("work_type")
                if not work_type or work_type == "Unspecified":
                    full_text = raw_summary + " " + (job.get("raw_text") or "")
                    from src.scraper.classifier import extract_work_type
                    work_type = extract_work_type(full_text)

                modality_badge = f" • <em>{work_type}</em>" if work_type and work_type != "Unspecified" else ""

                content += f"""
                <blockquote>
                <strong>{title}</strong><br>
                <small>Source: {channel}{modality_badge}</small>
                {f'<p>{body}</p>' if body else ''}
                <p><a href="{link}">👉 Apply / Open Telegram Post</a></p>
                </blockquote>
                """
                total_jobs_added += 1

        content += """
        <hr>
        <p><small>Delivered by <strong>Career Fit Jobs Bot</strong>. Manage your career alerts in the bot anytime.</small></p>
        """

        response = telegraph.create_page(
            title=f"Career Fit Jobs • {current_date}",
            html_content=content,
            author_name="Career Fit Jobs",
            return_content=True,
        )
        return response.get("url", "")
    except Exception as e:
        logger.error(f"Error creating Telegraph Instant View page: {e}")
        return ""
