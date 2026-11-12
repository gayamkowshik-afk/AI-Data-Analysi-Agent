"""Step 5: create the extra columns that make analysis easier."""
import numpy as np
import pandas as pd
from .utils import find_measure, add_log


def transform(df):
    d, log = df.copy(), []

    # Time columns allow trend analysis (monthly sales, growth).
    dates = [c for c in d.columns if pd.api.types.is_datetime64_any_dtype(d[c])]
    if dates:
        d["Year"] = d[dates[0]].dt.year
        d["Month"] = d[dates[0]].dt.month
        d["YearMonth"] = d[dates[0]].dt.strftime("%Y-%m")
        add_log(log, "Derive", "Year, Month, YearMonth", len(d), f"from {dates[0]}")

    # Margin shows profitability, which total profit alone hides.
    sales = find_measure(d, "sales") or find_measure(d, "revenue")
    profit = find_measure(d, "profit")
    if sales and profit:
        d["Profit_Margin_%"] = np.where(d[sales] != 0, d[profit] / d[sales] * 100, np.nan)
        add_log(log, "Derive", "Profit_Margin_%", len(d), f"{profit} / {sales} x 100")
    return d, log
