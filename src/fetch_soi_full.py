import pandas as pd

from src.filing_summary import parse_filing_summary
from src.soi_table import find_header_row, collapse_grouped_columns, classify_and_assign


def find_soi_page_tables(all_tables: list[pd.DataFrame]) -> list[int]:
    return find_soi_page_tables_generic(all_tables, ["Business Description", "Coupon", "Fair Value"])


def find_soi_page_tables_generic(all_tables: list[pd.DataFrame], required_terms: list[str]) -> list[int]:
    candidates = []
    for i, t in enumerate(all_tables):
        flat = t.values.flatten()
        text_blob = " ".join(str(v) for v in flat)
        if all(term in text_blob for term in required_terms):
            candidates.append(i)
    return candidates


def parse_all_soi_pages(all_tables: list[pd.DataFrame], page_indices: list[int]) -> pd.DataFrame:
    collapsed_pages = []
    for i in page_indices:
        raw = all_tables[i]
        try:
            hr = find_header_row(raw)
        except ValueError:
            continue
        clean_page = collapse_grouped_columns(raw, hr)
        clean_page["source_table"] = i
        collapsed_pages.append(clean_page)

        company_col = clean_page["Company"].astype(str)
        if company_col.str.strip().str.lower().str.startswith("total investments").any():
            break

    if not collapsed_pages:
        return pd.DataFrame()

    combined = pd.concat(collapsed_pages, ignore_index=True)
    return classify_and_assign(combined)


def to_float(val):
    if val is None or pd.isna(val):
        return None
    try:
        return float(str(val).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None
