import re
import pandas as pd

FOOTNOTE_PATTERN = re.compile(r"^(\(\d+\))+$")
LABEL_STRIP_PATTERN = re.compile(r"(\s*\(\d+\))+\s*$")


def find_header_row_generic(df: pd.DataFrame, required_terms: list[str]) -> int:
    for idx in range(len(df)):
        row_text = " ".join(str(v) for v in df.iloc[idx].values)
        if all(term in row_text for term in required_terms):
            return idx
    raise ValueError(f"header row not found for required terms {required_terms}")


def find_header_row(df: pd.DataFrame) -> int:
    return find_header_row_generic(df, ["Company", "Business Description"])


def build_column_groups(df: pd.DataFrame, header_row: int) -> list[str]:
    raw_labels = df.iloc[header_row].tolist()
    groups = []
    current_label = None
    for val in raw_labels:
        if not pd.isna(val) and str(val).strip():
            cleaned = LABEL_STRIP_PATTERN.sub("", str(val).strip())
            current_label = cleaned
        groups.append(current_label)
    return groups


def _clean_value(val):
    if pd.isna(val):
        return None
    text = str(val).strip()
    if text == "" or text == "$":
        return None
    if FOOTNOTE_PATTERN.match(text):
        return None
    return text


def _distinct_clean_values(row, cols):
    seen = []
    for c in cols:
        v = _clean_value(row[c])
        if v is not None and v not in seen:
            seen.append(v)
    return seen


def _join_clean_values(row, cols):
    values = _distinct_clean_values(row, cols)
    return " ".join(values) if values else None


def _extract_footnotes(row, cols):
    vals = []
    for c in cols:
        v = row[c]
        if pd.isna(v):
            continue
        text = str(v).strip()
        if FOOTNOTE_PATTERN.match(text):
            vals.append(text)
    return "".join(dict.fromkeys(vals)) if vals else None


def collapse_grouped_columns(df: pd.DataFrame, header_row: int) -> pd.DataFrame:
    groups = build_column_groups(df, header_row)
    body = df.iloc[header_row + 1:].reset_index(drop=True)

    label_to_indices: dict[str, list[int]] = {}
    for i, label in enumerate(groups):
        if label is None:
            continue
        label_to_indices.setdefault(label, []).append(i)

    result = {}
    for label, indices in label_to_indices.items():
        cols = [body.columns[i] for i in indices]
        if label == "Footnotes":
            result[label] = body.apply(lambda row, cols=cols: _extract_footnotes(row, cols), axis=1)
        else:
            result[label] = body.apply(lambda row, cols=cols: _join_clean_values(row, cols), axis=1)

    if "Footnotes" not in label_to_indices and "Fair Value" in label_to_indices:
        fv_cols = [body.columns[i] for i in label_to_indices["Fair Value"]]
        result["Footnotes"] = body.apply(lambda row, cols=fv_cols: _extract_footnotes(row, cols), axis=1)

    return pd.DataFrame(result)


def classify_and_assign(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    current_sector = None
    current_company = None
    sectors = []
    companies = []
    row_types = []

    for _, row in df.iterrows():
        has_company = pd.notna(row["Company"])
        has_investment = pd.notna(row["Investment"])
        has_financials = pd.notna(row["Amortized Cost"]) or pd.notna(row["Fair Value"])
        is_grand_total = has_company and str(row["Company"]).strip().lower().startswith("total investments")

        if is_grand_total:
            row_types.append("grand_total")
            companies.append(None)
        elif has_company and not has_investment and not has_financials:
            current_sector = row["Company"]
            row_types.append("sector_header")
            companies.append(None)
        elif has_company:
            current_company = row["Company"]
            row_types.append("company_row")
            companies.append(current_company)
        elif has_investment:
            row_types.append("tranche_continuation")
            companies.append(current_company)
        elif has_financials:
            row_types.append("company_subtotal")
            companies.append(current_company)
        else:
            row_types.append("blank")
            companies.append(current_company)

        sectors.append(current_sector)

    df["Sector"] = sectors
    df["Company_Filled"] = companies
    df["RowType"] = row_types
    return df
