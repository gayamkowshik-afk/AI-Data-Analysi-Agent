"""Approval-gated data analyst app.  Run with:  streamlit run app.py

How it is organised (useful for reviewers):
  - steps/      one small file per analysis step, no Streamlit code inside, easy to unit-test
  - app.py      only the screens: it calls one step at a time and waits for the user's approval
  - audit log   every approval is recorded with time, step and action
"""
import datetime as dt
import pandas as pd
import streamlit as st
from steps import s1_load, s2_profile, s3_errors, s4_clean, s5_transform, s6_kpis, s7_charts, s8_report
from steps.utils import category_columns

st.set_page_config(page_title="Data Analyst Agent", page_icon="📊", layout="wide")
S = st.session_state  # keeps the data and current step between button clicks
for key, default in {"step": 0, "raw": None, "df": None, "log": [], "audit": [], "q0": 0, "reco": ""}.items():
    S.setdefault(key, default)

STEPS = ["Load & privacy", "Profile", "Error check", "Clean", "Transform", "KPIs", "Charts & insights", "Dashboard & report"]


def record(action):
    S.audit.append({"time": dt.datetime.now().strftime("%H:%M:%S"), "step": STEPS[S.step], "action": action})


def approve_button(action):
    # The gate: nothing moves forward until the user clicks.
    if st.button("✅ Approve & continue", type="primary", key=f"approve{S.step}"):
        record(action)
        S.step += 1
        st.rerun()


def explain(text):
    st.info(f"**What I'm doing:** {text}")


def metric_row(kpis):
    cols = st.columns(min(4, len(kpis)))
    for i, (label, value) in enumerate(kpis):
        cols[i % len(cols)].metric(label, value)


# ---- sidebar: progress + audit log ----
with st.sidebar:
    st.title("📊 Analyst Agent")
    for i, name in enumerate(STEPS):
        st.write(("✅ " if i < S.step else "▶️ " if i == S.step else "⬜ ") + f"{i + 1}. {name}")
    st.progress(S.step / (len(STEPS) - 1))
    st.caption("🔒 Runs locally. Your data is not sent anywhere.")
    if S.audit:
        st.download_button("Download audit log", pd.DataFrame(S.audit).to_csv(index=False), "audit_log.csv")
    if st.button("🔄 Restart"):
        S.clear()
        st.rerun()

# ---- Step 1: load ----
if S.step == 0:
    st.header("Step 1 · Load data & protect privacy")
    explain("Reading your file on this computer and flagging personal columns so you can drop them.")
    upload = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    if upload:
        S.raw = s1_load.read_file(upload)
    if st.button("Use sample messy dataset"):
        S.raw = pd.read_csv("sample_data/messy_sales.csv")
    if S.raw is not None:
        st.dataframe(S.raw.head(10), width="stretch")
        drop = st.multiselect("Columns to drop (personal data)", list(S.raw.columns),
                              default=s1_load.find_personal_columns(S.raw))
        if st.button("✅ Approve & continue", type="primary"):
            S.df = s1_load.drop_columns(S.raw, drop)
            S.q0 = s2_profile.quality_score(S.df)
            record(f"Loaded {S.raw.shape[0]} rows, {S.raw.shape[1]} columns; dropped {drop or 'nothing'}")
            S.step = 1
            st.rerun()

# ---- Step 2: profile ----
elif S.step == 1:
    st.header("Step 2 · Profile the data")
    explain("Counting rows, columns, data types, missing values and unique values.")
    a, b, c = st.columns(3)
    a.metric("Rows", f"{len(S.df):,}")
    b.metric("Columns", S.df.shape[1])
    c.metric("Data-quality score", f"{S.q0}%")
    st.dataframe(s2_profile.profile_table(S.df), width="stretch")
    approve_button("Reviewed profile")

# ---- Step 3: error check ----
elif S.step == 2:
    st.header("Step 3 · Error check")
    explain("Looking for problems. Nothing is changed in this step.")
    issues = s3_errors.find_issues(S.df)
    if len(issues):
        st.dataframe(issues, width="stretch")
    else:
        st.success("No issues found.")
    approve_button(f"Reviewed {len(issues)} issue types")

# ---- Step 4: clean ----
elif S.step == 3:
    st.header("Step 4 · Clean")
    explain("Applying the fixes you tick. Check the before/after, then approve to keep the result.")
    options = {
        "types": st.checkbox("Fix data types (numbers/dates stored as text)", True),
        "text": st.checkbox("Standardise text labels", True),
        "dups": st.checkbox("Remove duplicate rows", True),
        "neg": st.checkbox("Treat negative sales/quantity/price as invalid", True),
        "fill": st.checkbox("Fill missing values (median / most frequent)", True),
        "cap": st.checkbox("Cap outliers (IQR rule)", False),
    }
    cleaned, changes = s4_clean.clean(S.df, options)
    q_old, q_new = s2_profile.quality_score(S.df), s2_profile.quality_score(cleaned)
    a, b, c = st.columns(3)
    a.metric("Rows", len(cleaned), len(cleaned) - len(S.df))
    b.metric("Quality score", f"{q_new}%", f"{q_new - q_old:+.1f}")
    c.metric("Missing cells", int(cleaned.isna().sum().sum()), int(cleaned.isna().sum().sum() - S.df.isna().sum().sum()))
    st.subheader("Change log")
    st.dataframe(pd.DataFrame(changes), width="stretch")
    if st.button("✅ Approve & continue", type="primary"):
        S.df, S.log = cleaned, changes
        record(f"Applied {len(changes)} cleaning actions")
        S.step = 4
        st.rerun()

# ---- Step 5: transform ----
elif S.step == 4:
    st.header("Step 5 · Transform")
    explain("Adding helper columns (Year, Month, Profit margin) when the data has what is needed.")
    transformed, changes = s5_transform.transform(S.df)
    st.dataframe(pd.DataFrame(changes) if changes else pd.DataFrame({"note": ["Nothing to derive"]}), width="stretch")
    st.dataframe(transformed.head(10), width="stretch")
    if st.button("✅ Approve & continue", type="primary"):
        S.df, S.log = transformed, S.log + changes
        record(f"Added {len(changes)} derived columns")
        S.step = 5
        st.rerun()

# ---- Step 6: KPIs ----
elif S.step == 5:
    st.header("Step 6 · KPIs")
    explain("Calculating headline numbers with pandas. Each value can be traced back to the data.")
    metric_row(s6_kpis.calculate_kpis(S.df))
    approve_button("KPIs calculated")

# ---- Step 7: charts ----
elif S.step == 6:
    st.header("Step 7 · Charts & insights")
    explain("Drawing charts with a one-line takeaway under each.")
    for i, chart in enumerate(s7_charts.build_charts(S.df)):
        st.subheader(chart["title"])
        st.plotly_chart(chart["fig"], width="stretch", key=f"chart{i}")
        st.success(chart["insight"])
    approve_button("Charts reviewed")

# ---- Step 8: dashboard + report ----
else:
    st.header("Step 8 · Dashboard & report")
    explain("Interactive dashboard for business partners, plus a report you can send to other teams.")
    view, filters = S.df, []
    with st.expander("Filters"):
        for col in category_columns(S.df)[:3]:
            picked = st.multiselect(col, sorted(S.df[col].dropna().unique()), key=f"filter_{col}")
            if picked:
                view = view[view[col].isin(picked)]
                filters.append(f"{col} = {', '.join(map(str, picked))}")
    kpis, charts = s6_kpis.calculate_kpis(view), s7_charts.build_charts(view)
    metric_row(kpis)
    grid = st.columns(2)
    for i, chart in enumerate(charts):
        with grid[i % 2]:
            st.subheader(chart["title"])
            st.plotly_chart(chart["fig"], width="stretch", key=f"dash{i}")
            st.caption(chart["insight"])

    st.divider()
    st.subheader("Report for other teams")
    title = st.text_input("Report title", "Business Performance Analysis")
    author = st.text_input("Prepared by", "Your Name")
    objective = st.text_area("Objective", "Understand performance drivers and data quality to support decisions.")
    S.reco = st.text_area("Recommendations (one per line, edit freely)",
                          S.reco or "\n".join(c["insight"] for c in charts[:3]))
    report_html = s8_report.build_report(title, author, objective, view.shape, S.q0,
                                         s2_profile.quality_score(view), S.log, kpis, charts, S.reco, "; ".join(filters))
    a, b, c = st.columns(3)
    a.download_button("⬇️ Report (HTML, print to PDF)", report_html, "analysis_report.html", "text/html")
    b.download_button("⬇️ Cleaned data (CSV)", S.df.to_csv(index=False), "cleaned_data.csv")
    c.download_button("⬇️ Audit log (CSV)", pd.DataFrame(S.audit).to_csv(index=False), "audit_log.csv")
