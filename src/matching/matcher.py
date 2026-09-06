"""Core matching algorithms between scraped job listings and user preferences."""

from typing import Dict, List, Any


def match_jobs_with_preferences(
    jobs: List[Dict[str, Any]], preferences: List[str]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Match job listings against a list of category preferences (case-insensitive substring).
    Returns a dictionary mapping matched category names to lists of job dictionaries.
    """
    matches: Dict[str, List[Dict[str, Any]]] = {}
    if not preferences:
        return matches

    for job in jobs:
        content = (job.get("summary", "") + " " + (job.get("raw_text") or "")).lower()
        for pref in preferences:
            pref_clean = pref.strip()
            if pref_clean.lower() in content:
                if pref_clean not in matches:
                    matches[pref_clean] = []
                matches[pref_clean].append(job)

    return matches
