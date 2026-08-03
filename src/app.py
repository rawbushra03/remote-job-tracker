"""
Remote Job Tracker - Interactive Streamlit Dashboard.

Visualizes scraped RemoteOK job data with KPIs, filters, and Plotly charts.
Run with: streamlit run src/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
JOBS_PATH = DATA_DIR / "jobs.csv"
SAMPLE_PATH = DATA_DIR / "jobs_sample.csv"
PAGE_TITLE = "Remote Job Tracker"
PAGE_ICON = "💼"

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


def resolve_data_source() -> tuple[Path, str]:
    """
    Select the best available CSV data source.

    Priority:
        1. data/jobs.csv (live scraped data)
        2. data/jobs_sample.csv (bundled sample for cloud deploy)

    Returns:
        Tuple of (file path, human-readable source label).

    Raises:
        FileNotFoundError: If neither CSV file exists.
    """
    if JOBS_PATH.exists():
        return JOBS_PATH, "Live scraped data (`data/jobs.csv`)"

    if SAMPLE_PATH.exists():
        return SAMPLE_PATH, "Sample dataset (`data/jobs_sample.csv`)"

    raise FileNotFoundError(
        "No job data found. Expected `data/jobs.csv` or `data/jobs_sample.csv`."
    )


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, str]:
    """
    Load and preprocess job data from CSV.

    Returns:
        Tuple of (cleaned DataFrame, data source label).
    """
    try:
        data_path, source_label = resolve_data_source()
    except FileNotFoundError:
        st.error(
            "No job data available.\n\n"
            "Run the scraper locally to generate `data/jobs.csv`:\n\n"
            "`python src/scraper.py`"
        )
        st.stop()

    df = pd.read_csv(data_path)

    if df.empty:
        st.error(
            f"The selected data file is empty: `{data_path.name}`.\n\n"
            "Run the scraper to collect job listings:\n\n"
            "`python src/scraper.py`"
        )
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["salary_numeric"] = df["salary"].apply(_extract_salary_midpoint)
    df["tag_list"] = df["tags"].fillna("").apply(
        lambda value: [tag.strip() for tag in str(value).split(",") if tag.strip()]
    )
    return df, source_label


def render_data_source_banner(source_label: str) -> None:
    """Display which dataset is currently powering the dashboard."""
    if "sample" in source_label.lower():
        st.info(
            f"**Data source:** {source_label}. "
            "Run `python src/scraper.py` locally to load fresh RemoteOK listings."
        )
    else:
        st.success(f"**Data source:** {source_label}.")


def _extract_salary_midpoint(salary_text: str | float) -> float | None:
    """Extract numeric salary midpoint from formatted salary strings."""
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


def get_all_tags(df: pd.DataFrame) -> list[str]:
    """Return a sorted list of unique tags across all jobs."""
    tags = sorted({tag for tags in df["tag_list"] for tag in tags})
    return tags


def render_header() -> None:
    """Render the dashboard title and subtitle."""
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")
    st.markdown(
        "Interactive analytics dashboard for remote job listings scraped from "
        "[RemoteOK](https://remoteok.com). Built with Python, pandas, and Streamlit."
    )
    st.divider()


def render_kpis(df: pd.DataFrame) -> None:
    """Render top-level KPI metrics."""
    total_jobs = len(df)
    total_companies = df["company"].nunique()
    salary_series = df["salary_numeric"].dropna()
    avg_salary = salary_series.mean() if not salary_series.empty else None

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Jobs", f"{total_jobs:,}")
    col2.metric("Companies", f"{total_companies:,}")
    col3.metric(
        "Avg. Salary (USD)",
        f"${avg_salary:,.0f}" if avg_salary is not None else "N/A",
    )
    col4.metric(
        "Jobs with Salary",
        f"{int(df['salary_numeric'].notna().sum()):,}",
    )


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Render sidebar filters and return the filtered DataFrame.

    Args:
        df: Full jobs DataFrame.

    Returns:
        Filtered DataFrame based on user selections.
    """
    st.sidebar.header("Filters")

    all_tags = get_all_tags(df)
    all_companies = sorted(df["company"].dropna().unique())

    selected_tags = st.sidebar.multiselect(
        "Technologies / Tags",
        options=all_tags,
        default=[],
        help="Show jobs that include any of the selected tags.",
    )

    selected_companies = st.sidebar.multiselect(
        "Companies",
        options=all_companies,
        default=[],
        help="Show jobs from the selected companies.",
    )

    salary_only = st.sidebar.checkbox(
        "Only jobs with salary disclosed",
        value=False,
    )

    filtered = df.copy()

    if selected_tags:
        filtered = filtered[
            filtered["tag_list"].apply(lambda tags: any(tag in tags for tag in selected_tags))
        ]

    if selected_companies:
        filtered = filtered[filtered["company"].isin(selected_companies)]

    if salary_only:
        filtered = filtered[filtered["salary_numeric"].notna()]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** jobs")

    return filtered


def render_charts(df: pd.DataFrame) -> None:
    """Render interactive Plotly charts."""
    st.subheader("Analytics")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        company_counts = (
            df["company"].value_counts().head(10).reset_index()
        )
        company_counts.columns = ["company", "jobs"]

        fig_companies = px.bar(
            company_counts,
            x="jobs",
            y="company",
            orientation="h",
            title="Top 10 Companies by Job Postings",
            color="jobs",
            color_continuous_scale="Blues",
        )
        fig_companies.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=420,
        )
        st.plotly_chart(fig_companies, use_container_width=True)

    with chart_col2:
        tag_series = (
            df["tag_list"]
            .explode()
            .dropna()
            .value_counts()
            .head(12)
            .reset_index()
        )
        tag_series.columns = ["tag", "mentions"]

        fig_tags = px.bar(
            tag_series,
            x="mentions",
            y="tag",
            orientation="h",
            title="Top Technologies & Skills",
            color="mentions",
            color_continuous_scale="Greens",
        )
        fig_tags.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=420,
        )
        st.plotly_chart(fig_tags, use_container_width=True)

    daily_counts = (
        df.dropna(subset=["date"])
        .assign(posting_day=lambda frame: frame["date"].dt.date)
        .groupby("posting_day", as_index=False)
        .size()
        .rename(columns={"size": "jobs"})
    )

    if not daily_counts.empty:
        fig_timeline = px.line(
            daily_counts,
            x="posting_day",
            y="jobs",
            markers=True,
            title="Job Postings Over Time",
            color_discrete_sequence=["#7c3aed"],
        )
        fig_timeline.update_layout(height=380, xaxis_title="Date", yaxis_title="Jobs")
        st.plotly_chart(fig_timeline, use_container_width=True)

    salary_df = df.dropna(subset=["salary_numeric"])
    if not salary_df.empty:
        fig_salary = px.histogram(
            salary_df,
            x="salary_numeric",
            nbins=20,
            title="Salary Distribution (USD, disclosed listings only)",
            color_discrete_sequence=["#f97316"],
        )
        fig_salary.update_layout(
            height=380,
            xaxis_title="Salary (USD)",
            yaxis_title="Number of Jobs",
        )
        st.plotly_chart(fig_salary, use_container_width=True)


def render_jobs_table(df: pd.DataFrame) -> None:
    """Render a searchable table of filtered job listings."""
    st.subheader("Job Listings")

    display_df = df[
        ["title", "company", "tags", "salary", "date", "link"]
    ].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values("date", ascending=False, na_position="last")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Job Title", width="medium"),
            "company": st.column_config.TextColumn("Company", width="small"),
            "tags": st.column_config.TextColumn("Tags", width="medium"),
            "salary": st.column_config.TextColumn("Salary", width="small"),
            "date": st.column_config.TextColumn("Posted", width="small"),
            "link": st.column_config.LinkColumn("Apply", display_text="Open"),
        },
    )


def main() -> None:
    """Build and render the Streamlit dashboard."""
    df, source_label = load_data()
    render_header()
    render_data_source_banner(source_label)
    filtered_df = apply_filters(df)
    render_kpis(filtered_df)

    if filtered_df.empty:
        st.warning("No jobs match the selected filters. Try adjusting your filters.")
        return

    render_charts(filtered_df)
    render_jobs_table(filtered_df)

    st.divider()
    st.caption(
        "Data source: [RemoteOK](https://remoteok.com) | "
        "Author: Bushra Rawat | "
        "Built for portfolio demonstration"
    )


if __name__ == "__main__":
    main()
