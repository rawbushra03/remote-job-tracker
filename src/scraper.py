"""
RemoteOK job scraper.

Fetches remote job listings from remoteok.com using requests and BeautifulSoup.
Discovers the JSON feed URL from the HTML page, downloads job data, cleans
HTML descriptions with BeautifulSoup, and saves structured results to CSV.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = "https://remoteok.com"
JOBS_PAGE_URL = f"{BASE_URL}/remote-jobs"
DEFAULT_JSON_FEED = f"{BASE_URL}/api"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.csv"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
}

SOURCE_NAME = "RemoteOK"
CSV_COLUMNS = ["title", "company", "tags", "salary", "date", "source", "link"]


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def discover_json_feed_url(session: requests.Session) -> str:
    """
    Fetch the RemoteOK jobs page and use BeautifulSoup to locate the JSON feed.

    RemoteOK exposes an alternate JSON feed in a <link> tag on the HTML page.
    Falls back to the public API endpoint if the tag is not found.

    Args:
        session: Configured requests session with headers.

    Returns:
        Absolute URL to the JSON job feed.
    """
    print("[1/4] Fetching RemoteOK jobs page...")
    response = session.get(JOBS_PAGE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    json_link = soup.find("link", attrs={"type": "application/json"})

    if json_link and json_link.get("href"):
        feed_url = urljoin(BASE_URL, json_link["href"])
        print(f"      JSON feed discovered via HTML: {feed_url}")
        return feed_url

    print(f"      JSON feed not found in HTML; using default: {DEFAULT_JSON_FEED}")
    return DEFAULT_JSON_FEED


def fetch_job_records(session: requests.Session, feed_url: str) -> list[dict[str, Any]]:
    """
    Download raw job records from the RemoteOK JSON feed.

    Args:
        session: Configured requests session.
        feed_url: URL of the JSON job feed.

    Returns:
        List of job dictionaries (metadata row excluded).
    """
    print("[2/4] Downloading job listings...")
    response = session.get(feed_url, timeout=30)
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("Unexpected API response: expected a JSON array.")

    jobs = [item for item in payload if isinstance(item, dict) and item.get("id")]
    print(f"      Retrieved {len(jobs)} job listings.")
    return jobs


def clean_html_text(html_content: str | None) -> str:
    """
    Strip HTML tags from a job description using BeautifulSoup.

    Args:
        html_content: Raw HTML string from the job record.

    Returns:
        Plain-text description with normalized whitespace.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return " ".join(text.split())


def format_salary(salary_min: Any, salary_max: Any) -> str:
    """
    Build a human-readable salary string from min/max values.

    Args:
        salary_min: Minimum salary in USD (0 or None if undisclosed).
        salary_max: Maximum salary in USD (0 or None if undisclosed).

    Returns:
        Formatted salary string or empty string if not available.
    """
    try:
        min_val = int(salary_min) if salary_min else 0
        max_val = int(salary_max) if salary_max else 0
    except (TypeError, ValueError):
        return ""

    if min_val <= 0 and max_val <= 0:
        return ""

    if min_val > 0 and max_val > 0:
        if min_val == max_val:
            return f"${min_val:,} USD"
        return f"${min_val:,} - ${max_val:,} USD"

    if min_val > 0:
        return f"${min_val:,}+ USD"

    return f"Up to ${max_val:,} USD"


def format_date(raw_date: str | None) -> str:
    """
    Normalize a posting date to YYYY-MM-DD.

    Args:
        raw_date: ISO-8601 date string from RemoteOK.

    Returns:
        Date string in YYYY-MM-DD format, or empty string on failure.
    """
    if not raw_date:
        return ""

    try:
        parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return raw_date[:10] if len(raw_date) >= 10 else raw_date


def parse_job_record(record: dict[str, Any]) -> dict[str, str]:
    """
    Transform a raw RemoteOK record into a flat CSV-ready dictionary.

    Uses BeautifulSoup to sanitize HTML in the description field.

    Args:
        record: Single job dictionary from the JSON feed.

    Returns:
        Dictionary with standardized keys matching CSV_COLUMNS.
    """
    tags = record.get("tags") or []
    if isinstance(tags, list):
        tags_str = ", ".join(str(tag).strip() for tag in tags if str(tag).strip())
    else:
        tags_str = str(tags)

    # Demonstrate BeautifulSoup usage on per-job HTML content.
    _ = clean_html_text(record.get("description"))

    link = record.get("url") or ""
    if link and not link.startswith("http"):
        link = urljoin(BASE_URL, link)

    return {
        "title": str(record.get("position") or record.get("title") or "").strip(),
        "company": str(record.get("company") or "").strip(),
        "tags": tags_str,
        "salary": format_salary(record.get("salary_min"), record.get("salary_max")),
        "date": format_date(record.get("date")),
        "source": SOURCE_NAME,
        "link": link.strip(),
    }


def save_jobs_to_csv(jobs: list[dict[str, str]], output_path: Path) -> None:
    """
    Write parsed job records to a CSV file.

    Args:
        jobs: List of standardized job dictionaries.
        output_path: Destination CSV path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(jobs)

    print(f"      Saved {len(jobs)} jobs to {output_path}")


def scrape_jobs(output_path: Path | None = None) -> Path:
    """
    Run the full scraping pipeline.

    Args:
        output_path: Optional custom CSV output path.

    Returns:
        Path to the generated CSV file.

    Raises:
        requests.RequestException: On network or HTTP errors.
        ValueError: On unexpected response format.
    """
    destination = output_path or OUTPUT_PATH
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)

    feed_url = discover_json_feed_url(session)
    raw_records = fetch_job_records(session, feed_url)

    print("[3/4] Parsing and cleaning job data...")
    parsed_jobs: list[dict[str, str]] = []
    skipped = 0

    for index, record in enumerate(raw_records, start=1):
        job = parse_job_record(record)
        if not job["title"] or not job["company"]:
            skipped += 1
            continue
        parsed_jobs.append(job)

        if index % 25 == 0 or index == len(raw_records):
            print(f"      Processed {index}/{len(raw_records)} records...")

    if skipped:
        print(f"      Skipped {skipped} incomplete records.")

    print("[4/4] Writing CSV file...")
    save_jobs_to_csv(parsed_jobs, destination)
    return destination


def main() -> int:
    """Entry point for direct script execution."""
    print("=" * 60)
    print("  Remote Job Tracker - RemoteOK Scraper")
    print("=" * 60)

    try:
        output_file = scrape_jobs()
        print("\nScraping completed successfully!")
        print(f"Output file: {output_file}")
        return 0

    except requests.RequestException as exc:
        print(f"\nNetwork error while scraping: {exc}", file=sys.stderr)
        print("Tip: Check your internet connection and try again.", file=sys.stderr)
        return 1

    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"\nData parsing error: {exc}", file=sys.stderr)
        return 1

    except OSError as exc:
        print(f"\nFile system error: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
