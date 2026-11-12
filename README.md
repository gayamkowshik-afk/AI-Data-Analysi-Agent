# Data Analyst Agent

A Streamlit app that follows the workflow of a data analyst: load, profile, find errors, clean, transform,
calculate KPIs, chart, build a dashboard, and produce a report. Each step explains what it is doing and
waits for the user to approve before continuing. Every approval is saved to an audit log.

## Why it is built this way
- **Local and private.** All processing happens in pandas on the user's machine. No API keys, no cloud AI, no telemetry.
  Personal columns (name, email, phone) are flagged and can be dropped before analysis starts.
- **Traceable numbers.** KPIs and chart insights are calculated from the data, not written by a model.
- **Auditable cleaning.** Each fix is logged (what changed, which column, how many rows).
- **Easy to read and test.** One small file per step in `steps/`; the UI in `app.py` only calls them.

## Run it
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Click "Use sample messy dataset" or upload a CSV/Excel file, then approve each step.
At the end, download `analysis_report.html` (open it, then Print > Save as PDF), `cleaned_data.csv` and `audit_log.csv`.

Tests: `pytest -q`

## Project layout
| File | Step |
|---|---|
| `steps/s1_load.py` | Read file, flag and drop personal columns |
| `steps/s2_profile.py` | Column profile and data-quality score |
| `steps/s3_errors.py` | Detect duplicates, missing values, wrong types, inconsistent labels, impossible negatives, outliers |
| `steps/s4_clean.py` | One small function per fix, all logged |
| `steps/s5_transform.py` | Year/Month columns, profit margin |
| `steps/s6_kpis.py` | Totals, averages, margin, month-over-month growth, top category |
| `steps/s7_charts.py` | Trend, category, distribution, correlation charts with insights |
| `steps/s8_report.py` | Fixed-template HTML report |
| `steps/utils.py` | Guesses which columns are measures, categories and dates |
| `app.py` | Screens and approval buttons |

## Notes
- Column roles are guessed from names such as sales, revenue, profit, quantity, date, region, category.
  If a dataset uses other names, rename them first.
- The report loads the Plotly chart library from a CDN when opened (no data is sent). For offline use, change
  `include_plotlyjs='cdn'` to `True` in `steps/s8_report.py`.
- Possible extensions: SQL source, joining several files, forecasting, direct PDF export.
