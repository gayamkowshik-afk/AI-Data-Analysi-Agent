"""Step 1: load the file and protect personal data."""
import pandas as pd

PERSONAL_HINTS = ("name", "email", "phone", "mobile", "address", "ssn", "aadhaar", "aadhar", "passport", "dob")


def read_file(file):
    if str(file.name).lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file, encoding_errors="replace")


def find_personal_columns(df):
    # Privacy by design: personal columns are flagged before any analysis happens.
    # "product name" is skipped because it is business data, not personal data.
    return [c for c in df.columns
            if any(h in str(c).lower() for h in PERSONAL_HINTS) and "product" not in str(c).lower()]


def drop_columns(df, columns):
    return df.drop(columns=columns).reset_index(drop=True)
