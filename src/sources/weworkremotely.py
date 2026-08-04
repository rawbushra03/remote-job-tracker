"""
We Work Remotely job source.

We Work Remotely has no JSON API, but it publishes public RSS feeds. We parse
the main feed with BeautifulSoup (lxml-xml) and map items to the unified schema.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from . import base

SOURCE_NAME = "WeWorkRemotely"
# Combined feed across all categories.
RSS_URL = "https://weworkremotely.com/remote-jobs.rss"


def _split_title(raw_title: str) -> tuple[str, str]:
    """
    WWR titles look like "Company: Job Title". Split into (company, title).

    Falls back gracefully when the colon is missing.
    """
    if ":" in raw_title:
        company, _, title = raw_title.partition(":")
        return company.strip(), title.strip()
    return "", raw_title.strip()


def fetch() -> list[dict[str, str]]:
    """
    Fetch remote jobs from the We Work Remotely RSS feed.

    Returns:
        List of unified job dictionaries (empty list on failure).
    """
    session = base.build_session()
    response = session.get(RSS_URL, timeout=base.REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "lxml-xml")
    items = soup.find_all("item")

    jobs: list[dict[str, str]] = []
    for item in items:
        raw_title = item.title.get_text(strip=True) if item.title else ""
        company, title = _split_title(raw_title)

        # Some feeds provide a dedicated <company> or <region> node.
        company_node = item.find("company")
        if company_node and company_node.get_text(strip=True):
            company = company_node.get_text(strip=True)

        region_node = item.find("region")
        category_node = item.find("category")
        tags = []
        if region_node and region_node.get_text(strip=True):
            tags.append(region_node.get_text(strip=True))
        for cat in item.find_all("category"):
            text = cat.get_text(strip=True)
            if text:
                tags.append(text)

        link = item.link.get_text(strip=True) if item.link else ""
        pub_date = item.pubDate.get_text(strip=True) if item.pubDate else ""

        job = base.make_job(
            title=title,
            company=company or "We Work Remotely",
            tags=base.normalize_tags(tags),
            salary="",
            date=base.format_date(pub_date),
            source=SOURCE_NAME,
            link=link,
        )
        if job["title"]:
            jobs.append(job)
    return jobs
