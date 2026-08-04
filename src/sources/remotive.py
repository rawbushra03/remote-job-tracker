"""
Remotive job source.

Uses the public Remotive API: https://remotive.com/api/remote-jobs
"""

from __future__ import annotations

from typing import Any

from . import base

SOURCE_NAME = "Remotive"
API_URL = "https://remotive.com/api/remote-jobs"


def _parse(record: dict[str, Any]) -> dict[str, str]:
    """Transform one Remotive record into the unified schema."""
    tags = record.get("tags") or []
    # Remotive also exposes a job category; fold it into the tag list.
    category = record.get("category")
    if category:
        tags = list(tags) + [category]

    return base.make_job(
        title=record.get("title"),
        company=record.get("company_name"),
        tags=base.normalize_tags(tags),
        # Remotive salary is a free-text string like "$50k - $70k".
        salary=base.format_salary(None, None, text=record.get("salary")),
        date=base.format_date(record.get("publication_date")),
        source=SOURCE_NAME,
        link=record.get("url"),
    )


def fetch() -> list[dict[str, str]]:
    """
    Fetch remote jobs from the Remotive API.

    Returns:
        List of unified job dictionaries (empty list on failure).
    """
    session = base.build_session()
    response = session.get(API_URL, timeout=base.REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    records = payload.get("jobs", []) if isinstance(payload, dict) else []
    jobs: list[dict[str, str]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        job = _parse(item)
        if job["title"] and job["company"]:
            jobs.append(job)
    return jobs
