"""
Shared helpers for all job sources.

Provides a common HTTP session, the unified CSV schema, and reusable
formatters for salary, dates, tags, and HTML cleaning so every source
produces rows in exactly the same shape.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Unified schema
# ---------------------------------------------------------------------------

# Every source must return dictionaries with exactly these keys.
UNIFIED_COLUMNS = ["title", "company", "tags", "salary", "date", "source", "link"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json,"
    "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 30


def build_session(referer: str | None = None) -> requests.Session:
    """
    Create a configured requests session shared by a source.

    Args:
        referer: Optional Referer header value (some APIs behave better with it).

    Returns:
        A ``requests.Session`` with sensible default headers.
    """
    session = requests.Session()
    headers = dict(DEFAULT_HEADERS)
    if referer:
        headers["Referer"] = referer
    session.headers.update(headers)
    return session


def clean_html_text(html_content: str | None) -> str:
    """
    Strip HTML tags from text using BeautifulSoup and normalize whitespace.

    Args:
        html_content: Raw HTML string (or None).

    Returns:
        Plain-text string with collapsed whitespace.
    """
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def normalize_tags(tags: Any, *, limit: int = 15) -> str:
    """
    Turn a list/string of tags into a clean, comma-separated string.

    Args:
        tags: A list of tags, a comma-separated string, or None.
        limit: Maximum number of tags to keep.

    Returns:
        Comma-separated tag string (lowercased, de-duplicated, trimmed).
    """
    items: list[str]
    if tags is None:
        items = []
    elif isinstance(tags, str):
        items = tags.split(",")
    elif isinstance(tags, Iterable):
        items = [str(tag) for tag in tags]
    else:
        items = [str(tags)]

    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in items:
        tag = str(raw).strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
        if len(cleaned) >= limit:
            break

    return ", ".join(cleaned)


def format_salary(salary_min: Any, salary_max: Any, *, text: str | None = None) -> str:
    """
    Build a human-readable salary string from min/max values or free text.

    Args:
        salary_min: Minimum salary (0/None if undisclosed).
        salary_max: Maximum salary (0/None if undisclosed).
        text: Optional pre-formatted salary text to fall back on.

    Returns:
        Formatted salary string, or empty string if nothing usable.
    """
    try:
        min_val = int(float(salary_min)) if salary_min else 0
        max_val = int(float(salary_max)) if salary_max else 0
    except (TypeError, ValueError):
        min_val = max_val = 0

    if min_val <= 0 and max_val <= 0:
        return (text or "").strip()

    if min_val > 0 and max_val > 0:
        if min_val == max_val:
            return f"${min_val:,} USD"
        return f"${min_val:,} - ${max_val:,} USD"

    if min_val > 0:
        return f"${min_val:,}+ USD"

    return f"Up to ${max_val:,} USD"


def format_date(raw_date: Any) -> str:
    """
    Normalize a posting date to YYYY-MM-DD.

    Accepts ISO-8601 strings, unix timestamps (int/float/numeric string),
    and RFC-822 strings (e.g. RSS ``pubDate``).

    Args:
        raw_date: Date value in one of several common formats.

    Returns:
        Date string in YYYY-MM-DD format, or empty string on failure.
    """
    if raw_date is None or raw_date == "":
        return ""

    # Unix timestamp (int/float, or a numeric string).
    if isinstance(raw_date, (int, float)) or (
        isinstance(raw_date, str) and raw_date.strip().isdigit()
    ):
        try:
            ts = int(float(raw_date))
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return ""

    text = str(raw_date).strip()

    # ISO-8601 (handles trailing Z).
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # RFC-822 (RSS pubDate, e.g. "Mon, 04 Aug 2026 12:00:00 +0000").
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Last resort: keep the first 10 chars if they look like a date.
    return text[:10] if len(text) >= 10 else ""


def make_job(
    *,
    title: Any,
    company: Any,
    tags: Any,
    salary: str,
    date: str,
    source: str,
    link: Any,
) -> dict[str, str]:
    """
    Assemble a unified job dict, trimming and coercing every field to str.

    Returns:
        A dictionary keyed by ``UNIFIED_COLUMNS``.
    """
    return {
        "title": str(title or "").strip(),
        "company": str(company or "").strip(),
        "tags": str(tags or "").strip(),
        "salary": str(salary or "").strip(),
        "date": str(date or "").strip(),
        "source": str(source or "").strip(),
        "link": str(link or "").strip(),
    }
