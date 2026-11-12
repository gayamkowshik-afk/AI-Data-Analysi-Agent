"""Runs the whole pipeline on the messy sample file and checks each step did its job."""
import pandas as pd
from steps import s1_load, s2_profile, s3_errors, s4_clean, s5_transform, s6_kpis, s7_charts, s8_report


def test_pipeline_end_to_end():
    raw = pd.read_csv("sample_data/messy_sales.csv")
    df = s1_load.drop_columns(raw, s1_load.find_personal_columns(raw))
    assert "Email" not in df.columns

    before = s2_profile.quality_score(df)
    assert len(s3_errors.find_issues(df)) > 0

    df, log = s4_clean.clean(df, dict(types=1, text=1, dups=1, neg=1, fill=1, cap=0))
    assert s2_profile.quality_score(df) > before
    assert df.duplicated().sum() == 0 and df["Region"].nunique() == 4

    df, log2 = s5_transform.transform(df)
    assert "YearMonth" in df

    kpis, charts = s6_kpis.calculate_kpis(df), s7_charts.build_charts(df)
    assert len(kpis) >= 5 and len(charts) >= 3
    html = s8_report.build_report("T", "A", "obj", df.shape, before, 99, log + log2, kpis, charts, "- a")
    assert "<html" in html
