"""Step 8: build the report for other teams as a single HTML file (print to PDF from the browser).

The layout is fixed on purpose, so every report looks the same and readers know where to look."""
import html
import datetime as dt

STYLE = """body{font-family:Segoe UI,Arial,sans-serif;max-width:980px;margin:30px auto;color:#222;line-height:1.5;padding:0 16px}
h1{border-bottom:3px solid #2563eb;padding-bottom:6px}h2{color:#1d4ed8;margin-top:32px}
.kpis{display:flex;flex-wrap:wrap;gap:12px}.kpi{background:#f1f5f9;border-radius:8px;padding:12px 16px;min-width:150px}
.kpi b{display:block;font-size:22px}.kpi span{font-size:12px;color:#555}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border:1px solid #ddd;padding:6px 8px;text-align:left}
th{background:#e2e8f0}.insight{background:#eff6ff;border-left:4px solid #2563eb;padding:8px 12px;margin:6px 0 24px}
.small{color:#666;font-size:12px}"""

LIMITATIONS = ("Results depend on the quality of the source data.\n"
               "Missing values were filled (median/mode) as listed in the cleaning table.\n"
               "Correlation does not imply causation.")


def _e(x):
    return html.escape(str(x))


def _bullets(text):
    return "".join(f"<li>{_e(line.strip('•- '))}</li>" for line in text.splitlines() if line.strip())


def build_report(title, author, objective, shape, quality_before, quality_after,
                 change_log, kpis, charts, recommendations, filters=""):
    kpi_cards = "".join(f"<div class='kpi'><b>{_e(v)}</b><span>{_e(k)}</span></div>" for k, v in kpis)

    if change_log:
        head = "".join(f"<th>{_e(h)}</th>" for h in change_log[0])
        body = "".join("<tr>" + "".join(f"<td>{_e(v)}</td>" for v in row.values()) + "</tr>" for row in change_log)
        log_table = f"<table><tr>{head}</tr>{body}</table>"
    else:
        log_table = "<p>No changes were applied.</p>"

    # The Plotly library is loaded once (first chart); the rest reuse it.
    chart_html = "".join(
        f"<h3>{_e(c['title'])}</h3>{c['fig'].to_html(full_html=False, include_plotlyjs='cdn' if i == 0 else False)}"
        f"<div class='insight'>{_e(c['insight'])}</div>" for i, c in enumerate(charts))
    filter_text = f"<br>Filters applied: {_e(filters)}" if filters else ""

    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{_e(title)}</title><style>{STYLE}</style></head><body>
<h1>{_e(title)}</h1><p class='small'>Prepared by {_e(author)} on {dt.date.today():%d %b %Y}</p>
<h2>1. Objective</h2><p>{_e(objective)}</p>
<h2>2. Data summary</h2><p>{shape[0]:,} rows and {shape[1]} columns analysed. Data-quality score improved from
<b>{quality_before}%</b> to <b>{quality_after}%</b> after cleaning.{filter_text}</p>
<h2>3. Cleaning and transformation</h2>{log_table}
<h2>4. Key KPIs</h2><div class='kpis'>{kpi_cards}</div>
<h2>5. Charts and insights</h2>{chart_html}
<h2>6. Recommendations</h2><ul>{_bullets(recommendations)}</ul>
<h2>7. Limitations</h2><ul>{_bullets(LIMITATIONS)}</ul>
</body></html>"""
