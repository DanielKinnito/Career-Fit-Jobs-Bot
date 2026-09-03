"""Notifier package for distributing matched job alerts."""

from .runner import run, match_jobs_with_preferences

__all__ = ["run", "match_jobs_with_preferences"]
