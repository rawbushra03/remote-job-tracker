"""
Arbeitnow job source.

Uses the public Arbeitnow job board API:
https://arbeitnow.com/api/job-board-api
"""

from __future__ import annotations

from typing import Any

from . import base

SOURCE_NAME = "Arbeitnow"
API_URL = "https://www.arbeitnow.com/api/job-board-api"


def _parse(record: dict[str, Any]) -> dict[str, str]:
    """Transform one Arbeitnow record into the unified schema."""
    tags = list(record.get("tags") or [])
    job_types = record.get("job_types") or []
    if job_types:
        tags += list(job_types)

    return base.make_job(
        title=record.get("title"),
        company=record.get("company_name"),
        tags=base.normalize_tags(tags),
        salary="",  # Arbeitnow does not expose structured salary
        date=base.format_date(record.get("created_at")),
        source=SOURCE_NAME,
        link=record.get("url"),
    )


def fetch() -> list[dict[str, str]]:
    """
    Fetch remote jobs from the Arbeitnow API.

    Only jobs flagged as ``remote`` are kept.

    Returns:
        List of unified job dictionaries (empty list on failure).
    """
    session = base.build_session()
    response = session.get(API_URL, timeout=base.REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    records = payload.get("data", []) if isinstance(payload, dict) else []
    jobs: list[dict[str, str]] = []
    for item in records:
        if not isinstance(item, dict):
            continue
        if not item.get("remote", False):
            continue  # keep only remote roles
        job = _parse(item)
        if job["title"] and job["company"]:
            jobs.append(job)
    return jobs
