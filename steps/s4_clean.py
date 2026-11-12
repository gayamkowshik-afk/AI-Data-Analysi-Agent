"""Step 4: clean the data. One small function per fix, so each rule is easy to read and test."""
import numpy as np
import pandas as pd
from .utils import text_columns, date_columns, numeric_ratio, measure_columns, add_log, NEGATIVE_NOT_ALLOWED


def fix_types(d, log):
    dates = date_columns(d)
    for c in text_columns(d):
        if c in dates:
            parsed = pd.to_datetime(d[c], errors="coerce", format="mixed")
            add_log(log, "Fix type", c, parsed.isna().sum() - d[c].isna().sum(), "unreadable dates set to missing")
            d[c] = parsed
        elif numeric_ratio(d[c].dropna()) > 0.8:
            d[c] = pd.to_numeric(d[c].astype(str).str.replace(r"[,$₹%\s]", "", regex=True), errors="coerce")
            add_log(log, "Fix type", c, d[c].notna().sum(), "text converted to numbers")
    return d


def standardise_text(d, log):
    # Variants such as " east ", "EAST" and "East" are mapped to the most common spelling.
    for c in text_columns(d):
        if d[c].nunique() > 100:
            continue  # free text (names, comments) should be left alone
        has_value = d[c].notna()
        original = d[c][has_value].astype(str).str.strip()
        key = original.str.lower().str.replace(r"\s+", " ", regex=True)
        most_common = original.groupby(key).agg(lambda x: x.value_counts().idxmax())
        fixed = d[c].copy()
        fixed[has_value] = key.map(most_common).values
        add_log(log, "Standardise text", c, ((fixed != d[c]) & has_value).sum(), "spaces/case unified")
        d[c] = fixed
    return d


def remove_duplicates(d, log):
    before = len(d)
    d = d.drop_duplicates().reset_index(drop=True)
    add_log(log, "Remove duplicates", "(all)", before - len(d), "exact repeated rows dropped")
    return d


def remove_negatives(d, log):
    for c in d.select_dtypes("number").columns:
        if any(h in str(c).lower() for h in NEGATIVE_NOT_ALLOWED):
            bad = d[c] < 0
            add_log(log, "Impossible negatives", c, bad.sum(), "set to missing")
            d.loc[bad, c] = np.nan
    return d


def fill_missing(d, log):
    # Median for numbers (not skewed by outliers), most frequent value for text.
    # Dates are left empty because inventing a date would be misleading.
    for c in d.columns:
        n = d[c].isna().sum()
        if n == 0 or pd.api.types.is_datetime64_any_dtype(d[c]):
            continue
        if pd.api.types.is_numeric_dtype(d[c]):
            d[c] = d[c].fillna(d[c].median())
            add_log(log, "Fill missing", c, n, "median")
        else:
            mode = d[c].mode()
            d[c] = d[c].fillna(mode.iloc[0] if len(mode) else "Unknown")
            add_log(log, "Fill missing", c, n, "most frequent value")
    return d


def cap_outliers(d, log):
    # Capping keeps every row but limits extreme values, which is safer than deleting data.
    for c in measure_columns(d):
        q1, q3 = d[c].quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        add_log(log, "Cap outliers", c, ((d[c] < low) | (d[c] > high)).sum(), f"limited to {low:.1f} .. {high:.1f}")
        d[c] = d[c].clip(low, high)
    return d


def clean(df, options):
    """Run the fixes the user ticked, in a sensible order. Returns (clean_df, change_log)."""
    d, log = df.copy().reset_index(drop=True), []
    order = [("types", fix_types), ("text", standardise_text), ("dups", remove_duplicates),
             ("neg", remove_negatives), ("fill", fill_missing), ("cap", cap_outliers)]
    for key, fix in order:
        if options.get(key):
            d = fix(d, log)
    return d, log
