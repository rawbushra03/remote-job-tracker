"""
RemoteOK job source.

Discovers the JSON feed from the HTML page with BeautifulSoup (falling back to
the public API endpoint) and returns unified job records.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from . import base

SOURCE_NAME = "RemoteOK"
BASE_URL = "https://remoteok.com"
JOBS_PAGE_URL = f"{BASE_URL}/remote-jobs"
DEFAULT_JSON_FEED = f"{BASE_URL}/api"


def _discover_feed_url(session) -> str:
    """Locate the JSON feed link on the HTML page, or fall back to the API."""
    from bs4 import BeautifulSoup

    try:
        response = session.get(JOBS_PAGE_URL, timeout=base.REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        json_link = soup.find("link", attrs={"type": "application/json"})
        if json_link and json_link.get("href"):
            return urljoin(BASE_URL, json_link["href"])
    except Exception:
        pass
    return DEFAULT_JSON_FEED


def _parse(record: dict[str, Any]) -> dict[str, str]:
    """Transform one RemoteOK record into the unified schema."""
    link = record.get("url") or ""
    if link and not link.startswith("http"):
        link = urljoin(BASE_URL, link)

    return base.make_job(
        title=record.get("position") or record.get("title"),
        company=record.get("company"),
        tags=base.normalize_tags(record.get("tags")),
        salary=base.format_salary(record.get("salary_min"), record.get("salary_max")),
        date=base.format_date(record.get("date")),
        source=SOURCE_NAME,
        link=link,
    )


def fetch() -> list[dict[str, str]]:
    """
    Fetch remote jobs from RemoteOK.

    Returns:
        List of unified job dictionaries (empty list on failure).
    """
    session = base.build_session(referer=BASE_URL)
    feed_url = _discover_feed_url(session)

    response = session.get(feed_url, timeout=base.REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list):
        return []

    jobs: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict) or not item.get("id"):
            continue  # first element is feed metadata / legal notice
        job = _parse(item)
        if job["title"] and job["company"]:
            jobs.append(job)
    return jobs
