"""
Remote job data analyzer.

Reads scraped job data from CSV, prints summary statistics to the console,
and generates static matplotlib charts saved to the screenshots directory.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "jobs.csv"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

CHART_DPI = 150
CHART_STYLE = "seaborn-v0_8-whitegrid"


def load_jobs(csv_path: Path | None = None) -> pd.DataFrame:
    """
    Load job listings from CSV into a pandas DataFrame.

    Args:
        csv_path: Optional path to the jobs CSV file.

    Returns:
        DataFrame with parsed date column and salary metadata.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is empty or malformed.
    """
    path = csv_path or DATA_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"Jobs file not found: {path}\n"
            "Run the scraper first: python src/scraper.py"
        )

    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"The jobs file is empty: {path}")

    required_columns = {"title", "company", "tags", "salary", "date", "link"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["salary_numeric"] = df["salary"].apply(extract_salary_midpoint)
    df["has_salary"] = df["salary_numeric"].notna()

    return df


def extract_salary_midpoint(salary_text: str | float) -> float | None:
    """
    Extract a numeric midpoint from a formatted salary string.

    Args:
        salary_text: Salary string such as '$80,000 - $120,000 USD'.

    Returns:
        Midpoint salary as float, or None if not parseable.
    """
    if pd.isna(salary_text) or not str(salary_text).strip():
        return None

    text = str(salary_text).replace(",", "").replace("USD", "").replace("$", "")
    numbers: list[float] = []

    for token in text.replace("-", " ").replace("+", " ").split():
        try:
            numbers.append(float(token))
        except ValueError:
            continue

    if not numbers:
        return None

    return sum(numbers) / len(numbers)


def explode_tags(df: pd.DataFrame) -> pd.Series:
    """
    Split comma-separated tags into individual lowercase tokens.

    Args:
        df: Jobs DataFrame with a 'tags' column.

    Returns:
        Series of individual tag strings.
    """
    tags = (
        df["tags"]
        .fillna("")
        .astype(str)
        .str.split(",")
        .explode()
        .str.strip()
        .str.lower()
    )
    return tags[tags != ""]


def print_summary_statistics(df: pd.DataFrame) -> None:
    """
    Print key analytics to the console.

    Args:
        df: Jobs DataFrame.
    """
    print("=" * 60)
    print("  Remote Job Tracker - Data Analysis Summary")
    print("=" * 60)

    total_jobs = len(df)
    total_companies = df["company"].nunique()
    jobs_with_salary = int(df["has_salary"].sum())
    avg_salary = df.loc[df["has_salary"], "salary_numeric"].mean()

    print(f"\nTotal jobs scraped     : {total_jobs:,}")
    print(f"Unique companies       : {total_companies:,}")
    print(f"Jobs with salary info  : {jobs_with_salary:,}")
    if pd.notna(avg_salary):
        print(f"Average salary (USD)   : ${avg_salary:,.0f}")
    else:
        print("Average salary (USD)   : N/A (no salary data)")

    print("\n--- Top 10 Companies ---")
    top_companies = df["company"].value_counts().head(10)
    for company, count in top_companies.items():
        print(f"  {company:<35} {count:>3} jobs")

    print("\n--- Top 15 Technologies / Tags ---")
    tag_counts = explode_tags(df).value_counts().head(15)
    for tag, count in tag_counts.items():
        print(f"  {tag:<35} {count:>3} mentions")

    print("\n--- Jobs Posted Per Day (last 14 days) ---")
    daily_counts = (
        df.dropna(subset=["date"])
        .assign(posting_day=lambda frame: frame["date"].dt.date)
        .groupby("posting_day")
        .size()
        .sort_index(ascending=False)
        .head(14)
    )

    if daily_counts.empty:
        print("  No valid posting dates found.")
    else:
        for day, count in daily_counts.items():
            print(f"  {day}  {count:>3} jobs")

    print()


def plot_top_companies(df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Create a horizontal bar chart of the top hiring companies.

    Args:
        df: Jobs DataFrame.
        output_dir: Directory for saved chart images.

    Returns:
        Path to the saved PNG file.
    """
    top_companies = df["company"].value_counts().head(10).sort_values()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_companies.index, top_companies.values, color="#2563eb")
    ax.set_title("Top 10 Companies by Job Postings", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Jobs")
    ax.set_ylabel("Company")

    for index, value in enumerate(top_companies.values):
        ax.text(value + 0.05, index, str(value), va="center", fontsize=9)

    fig.tight_layout()
    output_path = output_dir / "top_companies.png"
    fig.savefig(output_path, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_top_technologies(df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Create a bar chart of the most frequently mentioned technologies/tags.

    Args:
        df: Jobs DataFrame.
        output_dir: Directory for saved chart images.

    Returns:
        Path to the saved PNG file.
    """
    top_tags = explode_tags(df).value_counts().head(12).sort_values()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(top_tags.index, top_tags.values, color="#059669")
    ax.set_title("Top Technologies & Skills in Job Tags", fontsize=14, fontweight="bold")
    ax.set_xlabel("Mentions")
    ax.set_ylabel("Technology / Tag")

    fig.tight_layout()
    output_path = output_dir / "top_technologies.png"
    fig.savefig(output_path, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_jobs_by_day(df: pd.DataFrame, output_dir: Path) -> Path:
    """
    Create a line chart of daily job posting volume.

    Args:
        df: Jobs DataFrame.
        output_dir: Directory for saved chart images.

    Returns:
        Path to the saved PNG file.
    """
    daily = (
        df.dropna(subset=["date"])
        .assign(posting_day=lambda frame: frame["date"].dt.normalize())
        .groupby("posting_day")
        .size()
        .sort_index()
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily.index, daily.values, marker="o", linewidth=2, color="#7c3aed")
    ax.set_title("Remote Job Postings Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Posting Date")
    ax.set_ylabel("Number of Jobs")
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    output_path = output_dir / "jobs_by_day.png"
    fig.savefig(output_path, dpi=CHART_DPI, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_charts(df: pd.DataFrame, output_dir: Path | None = None) -> list[Path]:
    """
    Generate all matplotlib charts and save them to disk.

    Args:
        df: Jobs DataFrame.
        output_dir: Optional custom output directory.

    Returns:
        List of paths to generated chart files.
    """
    destination = output_dir or SCREENSHOTS_DIR
    destination.mkdir(parents=True, exist_ok=True)

    print("Generating charts...")
    charts = [
        plot_top_companies(df, destination),
        plot_top_technologies(df, destination),
        plot_jobs_by_day(df, destination),
    ]

    for chart_path in charts:
        print(f"  Saved: {chart_path.name}")

    return charts


def analyze(csv_path: Path | None = None) -> pd.DataFrame:
    """
    Run the full analysis pipeline.

    Args:
        csv_path: Optional path to the jobs CSV file.

    Returns:
        Loaded and enriched jobs DataFrame.
    """
    df = load_jobs(csv_path)
    print_summary_statistics(df)
    generate_charts(df)
    return df


def main() -> int:
    """Entry point for direct script execution."""
    try:
        plt.style.use(CHART_STYLE)
    except OSError:
        plt.style.use("ggplot")

    try:
        analyze()
        print("Analysis completed successfully!")
        print(f"Charts saved in: {SCREENSHOTS_DIR}")
        return 0

    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
