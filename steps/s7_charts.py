"""Step 7: charts, each with a one-line insight written from the numbers (not guessed)."""
import numpy as np
import plotly.express as px
from .utils import main_metric, find_measure, category_columns, measure_columns, fmt


def trend_chart(df, metric):
    monthly = df.groupby("YearMonth")[metric].sum().sort_index().reset_index()
    if len(monthly) < 3:
        return None
    half = len(monthly) // 2
    first, second = monthly[metric].iloc[:half].mean(), monthly[metric].iloc[half:].mean()
    change = (second / first - 1) * 100 if first else 0
    best, worst = monthly.loc[monthly[metric].idxmax()], monthly.loc[monthly[metric].idxmin()]
    return {"title": f"{metric} trend by month",
            "fig": px.line(monthly, x="YearMonth", y=metric, markers=True),
            "insight": f"Best month is {best['YearMonth']} ({fmt(best[metric])}), weakest is {worst['YearMonth']} "
                       f"({fmt(worst[metric])}). The second half averages {change:+.1f}% versus the first half."}


def category_chart(df, metric, group):
    totals = df.groupby(group)[metric].sum().sort_values(ascending=False).reset_index()
    total = totals[metric].sum()
    if not total:
        return None
    top, bottom = totals.iloc[0], totals.iloc[-1]
    insight = (f"{top[group]} contributes {top[metric] / total * 100:.1f}% of total {metric}; "
               f"{bottom[group]} contributes the least at {bottom[metric] / total * 100:.1f}%.")
    profit = find_measure(df, "profit")
    if profit and profit != metric:
        by_group = df.groupby(group)[profit].sum()
        losing = by_group[by_group < 0]
        if len(losing):
            insight += f" Loss-making {group}: {', '.join(map(str, losing.index))}."
    return {"title": f"{metric} by {group}", "fig": px.bar(totals, x=group, y=metric), "insight": insight}


def distribution_chart(df, metric):
    s = df[metric].dropna()
    if len(s) < 6:
        return None
    shape = "skewed by a few large values" if s.mean() > s.median() * 1.1 else "fairly balanced"
    return {"title": f"Distribution of {metric}", "fig": px.histogram(df, x=metric, nbins=30),
            "insight": f"Mean {fmt(s.mean())} vs median {fmt(s.median())}, so the data is {shape}."}


def correlation_chart(df):
    cols = measure_columns(df)
    if len(cols) < 3:
        return None
    corr = df[cols].corr()
    pairs = corr.where(np.triu(np.ones(corr.shape), 1).astype(bool)).stack()
    a, b = pairs.abs().idxmax()
    fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
    return {"title": "Correlation between numeric columns", "fig": fig,
            "insight": f"Strongest link is {a} vs {b} (r = {pairs.loc[(a, b)]:.2f}). Correlation is not causation."}


def build_charts(df):
    metric = main_metric(df)
    if not metric:
        return []
    charts = []
    if "YearMonth" in df:
        charts.append(trend_chart(df, metric))
    for group in category_columns(df)[:2]:
        charts.append(category_chart(df, metric, group))
    charts.append(distribution_chart(df, metric))
    charts.append(correlation_chart(df))
    return [c for c in charts if c]
