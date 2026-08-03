# 💼 Remote Job Tracker

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Analysis-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3D4F91?logo=plotly&logoColor=white)](https://plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> End-to-end Python project that scrapes remote job listings from [RemoteOK](https://remoteok.com), analyzes hiring trends with pandas, and presents insights through a professional Streamlit dashboard.

Built as a portfolio project to demonstrate skills in **web scraping**, **data analysis**, and **interactive data visualization**.

---

## ✨ Features

- **Web scraping pipeline** — Fetches live remote job listings from RemoteOK using `requests` and `BeautifulSoup`
- **Structured data export** — Saves job title, company, tags, salary, posting date, and apply link to CSV
- **Statistical analysis** — Computes top companies, trending technologies, and daily posting volume
- **Static visualizations** — Generates publication-ready charts with matplotlib
- **Interactive dashboard** — Streamlit app with KPIs, filters, and Plotly charts
- **Production-ready code** — Error handling, docstrings, modular architecture, and clear logging

---

## 📸 Screenshots

> Run `python src/analyzer.py` after scraping to generate chart images.

| Top Companies | Top Technologies | Jobs Over Time |
|:---:|:---:|:---:|
| ![Top Companies](screenshots/top_companies.png) | ![Top Technologies](screenshots/top_technologies.png) | ![Jobs by Day](screenshots/jobs_by_day.png) |

**Streamlit Dashboard** — run `streamlit run src/app.py` to explore the interactive UI locally.

---

## 🛠 Tech Stack

| Category | Tools |
|----------|-------|
| Web Scraping | `requests`, `BeautifulSoup4`, `lxml` |
| Data Analysis | `pandas` |
| Static Charts | `matplotlib` |
| Interactive Dashboard | `Streamlit`, `Plotly` |
| Language | Python 3.10+ |

---

## 📁 Project Structure

```
remote-job-tracker/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── scraper.py       # Scrape RemoteOK and save CSV
│   ├── analyzer.py      # Analyze data and generate charts
│   └── app.py           # Streamlit dashboard
├── data/
│   ├── .gitkeep
│   └── jobs_sample.csv  # Sample data (committed)
└── screenshots/
    └── .gitkeep         # Generated charts saved here
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/bushra-rawat/remote-job-tracker.git
cd remote-job-tracker
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 📖 Usage

### Step 1 — Scrape job listings

```bash
python src/scraper.py
```

This will:
- Fetch the RemoteOK jobs page and discover the JSON feed via HTML parsing
- Download and parse job listings
- Save results to `data/jobs.csv`

### Step 2 — Run data analysis

```bash
python src/analyzer.py
```

This will:
- Print summary statistics to the console
- Generate 3 charts in the `screenshots/` folder

### Step 3 — Launch the dashboard

```bash
streamlit run src/app.py
```

Open the URL shown in the terminal (typically `http://localhost:8501`) to explore the interactive dashboard.

---

## 📊 Sample Output

**Console statistics include:**
- Total jobs and unique companies
- Top 10 hiring companies
- Top 15 technologies / tags
- Jobs posted per day

**Dashboard features:**
- KPI cards (total jobs, companies, average salary)
- Filters by technology and company
- Interactive Plotly charts
- Sortable job listings table with apply links

---

## 🔮 Future Improvements

- [ ] Schedule automated daily scraping with cron or GitHub Actions
- [ ] Store historical data in SQLite for trend analysis over time
- [ ] Add email/Slack alerts for new jobs matching user-defined filters
- [ ] Expand data sources (We Work Remotely, Remotive, etc.)
- [ ] Deploy dashboard to Streamlit Community Cloud
- [ ] Add unit tests for scraper and analyzer modules

---

## ⚠️ Disclaimer

This project uses the public RemoteOK feed for educational and portfolio purposes. Please respect [RemoteOK's API terms of service](https://remoteok.com/api) — link back to RemoteOK when using their data publicly.

---

## 👩‍💻 Author

**Bushra Rawat**  
Systems Engineering Student | Aspiring Remote Developer

- 🔗 LinkedIn: [linkedin.com/in/bushra-rawat](https://www.linkedin.com/in/bushra-rawat)
- 🐙 GitHub: [github.com/bushra-rawat](https://github.com/bushra-rawat)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
