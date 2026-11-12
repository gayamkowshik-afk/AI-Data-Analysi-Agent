"""Small helpers shared by all steps.

Column roles (measure, category, date) are guessed from column names and data types,
so the same pipeline works on different datasets without hard-coding column names."""
import re
import pandas as pd

NEGATIVE_NOT_ALLOWED = ("sales", "revenue", "amount", "price", "cost", "quantity", "qty", "age", "salary")
METRIC_PRIORITY = ("sales", "revenue", "amount", "total", "income", "salary", "profit", "price")
CATEGORY_PRIORITY = ("region", "category", "segment", "department", "state", "country", "city", "channel")


def text_columns(df):
    # Works on both older and newer pandas, which store text differently.
    return [c for c in df.columns
            if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])]


def numeric_ratio(series):
    # Share of values that look like numbers once symbols like "," and "$" are removed.
    cleaned = series.astype(str).str.replace(r"[,$₹%\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce").notna().mean() if len(cleaned) else 0


def date_columns(df):
    real = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    as_text = [c for c in text_columns(df) if "date" in str(c).lower() or "time" in str(c).lower()]
    return real + [c for c in as_text if c not in real]


def is_id_column(name):
    # IDs, years, zip codes etc. are numbers but should never be summed or averaged.
    n = str(name).lower()
    return n.endswith("id") or bool(re.search(r"(^|[^a-z])id([^a-z]|$)|year|month|zip|postal|code|index", n))


def measure_columns(df):
    return [c for c in df.select_dtypes("number").columns if not is_id_column(c)]


def find_measure(df, hint):
    for c in measure_columns(df):
        if hint in c.lower() and "margin" not in c.lower():
            return c


def main_metric(df):
    # The column the dashboard is "about": sales/revenue first, then anything numeric.
    for hint in METRIC_PRIORITY:
        c = find_measure(df, hint)
        if c:
            return c
    cols = measure_columns(df)
    return cols[0] if cols else None


def category_columns(df):
    # Text columns with few distinct values (2-25) are good for grouping and filters.
    cols = [c for c in text_columns(df)
            if 2 <= df[c].nunique() <= 25 and c not in date_columns(df) and c != "YearMonth"]
    return sorted(cols, key=lambda c: 0 if any(h in c.lower() for h in CATEGORY_PRIORITY) else 1)


def add_log(log, step, column, rows, detail=""):
    # Every change is recorded so the cleaning can be audited and reproduced.
    if rows:
        log.append({"Step": step, "Column": column, "Rows affected": int(rows), "Detail": detail})


def fmt(x):
    # 1250000 -> 1.25M, so KPI cards stay readable.
    if x is None or pd.isna(x):
        return "n/a"
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(x) >= limit:
            return f"{x / limit:.2f}{suffix}"
    return f"{x:,.2f}" if x != int(x) else f"{int(x):,}"
