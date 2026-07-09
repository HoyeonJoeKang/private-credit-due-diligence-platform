import re
import pandas as pd


def _clean_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r"[\$,]", "", regex=True).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def find_value_columns(df: pd.DataFrame, label_col: str, threshold: float = 0.5) -> list[str]:
    value_cols = []
    for col in df.columns:
        if col == label_col:
            continue
        numeric = _clean_numeric_series(df[col])
        if numeric.notna().mean() > threshold:
            value_cols.append(col)
    return value_cols


def extract_total_investments_fair_value(df: pd.DataFrame, unit_multiplier: float = 1.0,
                                          label_candidates: tuple[str, ...] = ("fair value",)) -> dict:
    label_col = df.columns[0]
    labels = df[label_col].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    value_cols = find_value_columns(df, label_col)

    candidates_lower = [c.lower() for c in label_candidates]
    matches = df[labels.str.lower().isin(candidates_lower)]
    if matches.empty:
        raise ValueError(f"None of {label_candidates} found in balance sheet table")

    row = matches.iloc[0]
    result = {}
    for col in value_cols:
        val = _clean_numeric_series(pd.Series([row[col]])).iloc[0]
        if pd.notna(val):
            result[col] = val * unit_multiplier
    return result


def extract_line_item(df: pd.DataFrame, label_prefixes: tuple[str, ...],
                       unit_multiplier: float = 1.0) -> dict:
    label_col = df.columns[0]
    labels = df[label_col].apply(lambda x: str(x).strip() if pd.notna(x) else "")
    value_cols = find_value_columns(df, label_col)

    prefixes_lower = [p.lower() for p in label_prefixes]
    labels_lower = labels.str.lower()
    mask = labels_lower.apply(lambda label: any(label.startswith(p) for p in prefixes_lower))
    matches = df[mask]
    if matches.empty:
        raise ValueError(f"None of {label_prefixes} found as a label prefix in balance sheet table")

    row = matches.iloc[0]
    result = {}
    for col in value_cols:
        val = _clean_numeric_series(pd.Series([row[col]])).iloc[0]
        if pd.notna(val):
            result[col] = val * unit_multiplier
    return result


def detect_unit_multiplier(table_title: str) -> float:
    text = table_title.lower()
    if "in millions" in text:
        return 1_000_000.0
    if "in thousands" in text:
        return 1_000.0
    return 1.0
