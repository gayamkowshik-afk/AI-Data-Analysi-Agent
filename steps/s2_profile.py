"""Step 2: profile the data (what do we have?)."""
import pandas as pd
from .utils import text_columns


def profile_table(df):
    return pd.DataFrame({
        "dtype": df.dtypes.astype(str),
        "missing": df.isna().sum(),
        "missing_%": (df.isna().mean() * 100).round(1),
        "unique": df.nunique(),
    })


def quality_score(df):
    """One number (0-100) to show improvement before vs after cleaning.

    Formula: 100 minus the share of missing cells, minus the share of duplicate rows,
    minus a smaller penalty for text columns with inconsistent labels ("East" vs " east ")."""
    if df.empty:
        return 0.0
    missing = df.isna().sum().sum() / df.size
    duplicates = df.duplicated().sum() / len(df)
    messy = 0
    for c in text_columns(df):
        s = df[c].dropna().astype(str)
        if len(s) and s.nunique() > s.str.strip().str.lower().nunique():
            messy += 1
    messy_share = messy / df.shape[1]
    return round(max(0.0, 100 * (1 - missing - duplicates - 0.5 * messy_share)), 1)
