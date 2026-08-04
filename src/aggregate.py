"""
Multi-source job aggregator for Remote Job Tracker.

Runs every scraper in ``src/sources``, merges the results into the unified
schema, removes duplicates, sorts by most recent posting date, and writes a
single CSV consumed by the Streamlit dashboard.

Usage:
    python src/aggregate.py                 # write data/jobs.csv
    python src/aggregate.py --sample        # also refresh data/jobs_sample.csv
    python src/aggregate.py --max-jobs 500  # cap the number of rows written
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Allow running both as "python src/aggregate.py" and "python -m src.aggregate".
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.sources import SOURCE_MODULES  # noqa: E402
    from src.sources import base  # noqa: E402
else:
    from .sources import SOURCE_MODULES
    from .sources import base

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_PATH = DATA_DIR / "jobs.csv"
SAMPLE_PATH = DATA_DIR / "jobs_sample.csv"

DEFAULT_MAX_JOBS = 500


def _source_name(module) -> str:
    """Return the human-readable name declared by a source module."""
    return getattr(module, "SOURCE_NAME", module.__name__.split(".")[-1])


def collect_jobs() -> list[dict[str, str]]:
    """
    Run every source scraper and combine their results.

    A failure in one source never aborts the run; it is logged and skipped.

    Returns:
        A combined list of unified job dictionaries.
    """
    all_jobs: list[dict[str, str]] = []
    total_sources = len(SOURCE_MODULES)

    for index, module in enumerate(SOURCE_MODULES, start=1):
        name = _source_name(module)
        print(f"[{index}/{total_sources}] Fetching from {name}...")
        try:
            jobs = module.fetch()
            print(f"      Retrieved {len(jobs)} jobs from {name}.")
            all_jobs.extend(jobs)
        except Exception as exc:  # noqa: BLE001 - keep the pipeline resilient
            print(f"      WARNING: {name} failed ({exc}); skipping.", file=sys.stderr)

    return all_jobs


def deduplicate(jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Remove duplicate postings.

    A job is considered a duplicate if it shares the same apply link, or the
    same (title, company) pair (case-insensitive).

    Args:
        jobs: Combined list of job dictionaries.

    Returns:
        De-duplicated list, preserving first-seen order.
    """
    seen_links: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []

    for job in jobs:
        link = job.get("link", "").strip().lower()
        pair = (job.get("title", "").lower(), job.get("company", "").lower())

        if link and link in seen_links:
            continue
        if pair in seen_pairs:
            continue

        if link:
            seen_links.add(link)
        seen_pairs.add(pair)
        unique.append(job)

    return unique


def sort_by_recency(jobs: list[dict[str, str]]) -> list[dict[str, str]]:
    """Sort jobs by posting date, most recent first (blank dates last)."""
    return sorted(jobs, key=lambda job: job.get("date", ""), reverse=True)


def save_csv(jobs: list[dict[str, str]], output_path: Path) -> None:
    """
    Write jobs to a CSV file using the unified column order.

    Args:
        jobs: List of unified job dictionaries.
        output_path: Destination CSV path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=base.UNIFIED_COLUMNS)
        writer.writeheader()
        writer.writerows(jobs)
    print(f"      Saved {len(jobs)} jobs to {output_path}")


def run(
    *,
    output_path: Path | None = None,
    sample_path: Path | None = None,
    write_sample: bool = False,
    max_jobs: int = DEFAULT_MAX_JOBS,
) -> list[dict[str, str]]:
    """
    Execute the full aggregation pipeline.

    Args:
        output_path: Where to write the main CSV (defaults to data/jobs.csv).
        sample_path: Where to write the sample CSV (defaults to jobs_sample.csv).
        write_sample: Also overwrite the committed sample dataset.
        max_jobs: Maximum number of rows to keep after sorting.

    Returns:
        The final list of unified job dictionaries that were written.
    """
    destination = output_path or OUTPUT_PATH
    sample_destination = sample_path or SAMPLE_PATH

    print("=" * 60)
    print("  Remote Job Tracker - Multi-Source Aggregator")
    print("=" * 60)

    raw_jobs = collect_jobs()
    print(f"\nCombined total (raw): {len(raw_jobs)} jobs")

    unique_jobs = deduplicate(raw_jobs)
    print(f"After de-duplication: {len(unique_jobs)} jobs")

    ordered_jobs = sort_by_recency(unique_jobs)
    if max_jobs and len(ordered_jobs) > max_jobs:
        print(f"Capping to the {max_jobs} most recent jobs.")
        ordered_jobs = ordered_jobs[:max_jobs]

    # Per-source summary for quick sanity checks.
    counts: dict[str, int] = {}
    for job in ordered_jobs:
        counts[job["source"]] = counts.get(job["source"], 0) + 1
    print("\nJobs per source (written):")
    for source, count in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {source:<18} {count:>4}")

    print("\nWriting CSV...")
    save_csv(ordered_jobs, destination)

    if write_sample:
        save_csv(ordered_jobs, sample_destination)

    return ordered_jobs


def main() -> int:
    """Entry point for direct script execution."""
    parser = argparse.ArgumentParser(
        description="Aggregate remote jobs from multiple sources into a CSV."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Also overwrite data/jobs_sample.csv (used by the live dashboard).",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=DEFAULT_MAX_JOBS,
        help=f"Maximum number of jobs to keep (default: {DEFAULT_MAX_JOBS}).",
    )
    args = parser.parse_args()

    try:
        jobs = run(write_sample=args.sample, max_jobs=args.max_jobs)
        if not jobs:
            print("\nNo jobs were collected from any source.", file=sys.stderr)
            return 1
        print("\nAggregation completed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
