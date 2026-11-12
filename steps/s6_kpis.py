"""Step 6: headline KPIs. Every number comes from pandas, so it can be traced and verified."""
from .utils import main_metric, find_measure, category_columns, fmt


def calculate_kpis(df):
    kpis = [("Rows analysed", fmt(len(df)))]
    metric = main_metric(df)
    if not metric:
        return kpis

    kpis += [(f"Total {metric}", fmt(df[metric].sum())), (f"Average {metric}", fmt(df[metric].mean()))]

    profit = find_measure(df, "profit")
    if profit:
        kpis.append((f"Total {profit}", fmt(df[profit].sum())))
        if profit != metric and df[metric].sum():
            kpis.append(("Overall margin", f"{df[profit].sum() / df[metric].sum() * 100:.1f}%"))

    qty = find_measure(df, "quantity") or find_measure(df, "qty")
    if qty:
        kpis.append((f"Total {qty}", fmt(df[qty].sum())))

    if "YearMonth" in df:
        monthly = df.groupby("YearMonth")[metric].sum().sort_index()
        if len(monthly) >= 2 and monthly.iloc[-2]:
            growth = (monthly.iloc[-1] / monthly.iloc[-2] - 1) * 100
            kpis.append(("Latest month-over-month growth", f"{growth:+.1f}%"))

    groups = category_columns(df)
    if groups:
        kpis.append((f"Top {groups[0]}", str(df.groupby(groups[0])[metric].sum().idxmax())))
    return kpis
