"""Step 3: find data problems. This step only reports; it never changes the data."""
import pandas as pd
from .utils import text_columns, date_columns, numeric_ratio, NEGATIVE_NOT_ALLOWED


def _outlier_count(s):
    # IQR rule: values beyond 1.5 x the middle-50% range. Chosen over z-score because it
    # does not assume the data is normally distributed (sales data rarely is).
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum()) if iqr > 0 else 0


def find_issues(df):
    rows = []
    dupes = int(df.duplicated().sum())
    if dupes:
        rows.append(("Duplicate rows", "(all)", dupes, "Remove duplicates"))

    for c in df.columns:
        n = int(df[c].isna().sum())
        if n:
            rows.append(("Missing values", c, n, "Fill with median/mode"))

    for c in text_columns(df):
        s = df[c].dropna().astype(str)
        if s.empty:
            continue
        if c in date_columns(df):
            rows.append(("Dates stored as text", c, len(s), "Convert to datetime"))
        elif numeric_ratio(s) > 0.8:
            rows.append(("Numbers stored as text", c, len(s), "Convert to numeric"))
        else:
            tidy = s.str.strip().str.lower().str.replace(r"\s+", " ", regex=True)
            extra = s.nunique() - tidy.nunique()
            if extra > 0:
                rows.append(("Inconsistent labels", c, extra, "Standardise spelling/case"))

    for c in df.select_dtypes("number").columns:
        s = df[c].dropna()
        if s.empty:
            continue
        n = _outlier_count(s)
        if n:
            rows.append(("Outliers (IQR)", c, n, "Cap at IQR limits"))
        if any(h in str(c).lower() for h in NEGATIVE_NOT_ALLOWED) and (s < 0).any():
            rows.append(("Impossible negatives", c, int((s < 0).sum()), "Set to missing, then fill"))

    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            n = int((df[c] > pd.Timestamp.now()).sum())
            if n:
                rows.append(("Future dates", c, n, "Check the source"))

    return pd.DataFrame(rows, columns=["Issue", "Column", "Count", "Suggested fix"])
