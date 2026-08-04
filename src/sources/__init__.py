"""
Job source scrapers for Remote Job Tracker.

Each module in this package exposes a `fetch()` function that returns a list of
job dictionaries in the unified schema defined in ``base.UNIFIED_COLUMNS``:

    title, company, tags, salary, date, source, link

The aggregator (``src/aggregate.py``) calls every source, merges the results,
removes duplicates, and writes a single CSV consumed by the dashboard.
"""

from __future__ import annotations

from . import arbeitnow, remoteok, remotive, weworkremotely

# Ordered list of source modules the aggregator will run.
SOURCE_MODULES = [remoteok, remotive, arbeitnow, weworkremotely]

__all__ = [
    "SOURCE_MODULES",
    "remoteok",
    "remotive",
    "arbeitnow",
    "weworkremotely",
]
