import re
from datetime import datetime, timezone

import pandas as pd

from src.fetch_main_doc import fetch_main_document
from src.fetch_soi_full import find_soi_page_tables_generic, to_float
from src.soi_table import find_header_row_generic, collapse_grouped_columns
from src.soi_table_bxsl import classify_and_assign_bxsl
from src.footnote_legend import build_plain_text, find_non_accrual_footnote_candidates, footnotes_contain_number
from src.pipeline_phase4 import normalize_issuer_name, parse_pct

BXSL_SOI_REQUIRED_TERMS = ["Investments", "Fair Value", "Par Amount"]
BXSL_HEADER_REQUIRED_TERMS = ["Investments", "Fair Value"]


def find_soi_page_tables_bxsl(all_tables: list[pd.DataFrame]) -> list[int]:
    return find_soi_page_tables_generic(all_tables, BXSL_SOI_REQUIRED_TERMS)


def parse_all_soi_pages_bxsl(all_tables: list[pd.DataFrame], page_indices: list[int]) -> pd.DataFrame:
    collapsed_pages = []
    for i in page_indices:
        raw = all_tables[i]
        try:
            hr = find_header_row_generic(raw, BXSL_HEADER_REQUIRED_TERMS)
        except ValueError:
            continue
        clean_page = collapse_grouped_columns(raw, hr)
        clean_page["source_table"] = i
        collapsed_pages.append(clean_page)

        investments_col = clean_page["Investments"].astype(str)
        if investments_col.str.strip().str.lower().str.startswith("total portfolio investments").any():
            break

    if not collapsed_pages:
        return pd.DataFrame()

    combined = pd.concat(collapsed_pages, ignore_index=True)
    return classify_and_assign_bxsl(combined)


REF_SPREAD_PATTERN = re.compile(r"^(.*?)\+\s*([\d.]+)\s*%?\s*$")


def parse_reference_and_spread(text):
    if text is None or pd.isna(text):
        return None, None
    m = REF_SPREAD_PATTERN.match(str(text).strip())
    if not m:
        return str(text).strip(), None
    return m.group(1).strip(), float(m.group(2))


def process_filing_soi_bxsl(ticker: str, cik: str, accession: str, primary_doc_url: str,
                             period_end: str, conn, target_total: float | None,
                             unit_multiplier: float = 1.0) -> dict:
    main_doc_path = fetch_main_document(ticker, accession, primary_doc_url)
    all_tables = pd.read_html(main_doc_path)
    page_indices = find_soi_page_tables_bxsl(all_tables)
    full_soi = parse_all_soi_pages_bxsl(all_tables, page_indices)

    if full_soi.empty:
        return {"accession": accession, "status": "no_tables_found", "page_indices": page_indices}

    full_soi["Fair Value Num"] = full_soi["Fair Value"].apply(to_float)
    line_level = full_soi[full_soi["RowType"] == "company_row"].copy()

    asset_class_text = line_level["AssetClass"].astype(str).str.lower()
    sector_text = line_level["Sector"].astype(str).str.lower()
    is_cash_equivalent = asset_class_text.str.contains("cash", na=False) | sector_text.str.contains("cash", na=False)
    investment_only = line_level[~is_cash_equivalent]
    computed_total = investment_only["Fair Value Num"].sum() * unit_multiplier

    now = datetime.now(timezone.utc).isoformat()
    passed = None
    diff_pct = None
    if target_total is not None:
        diff_pct = (computed_total - target_total) / target_total * 100
        passed = abs(diff_pct) < 0.01
        conn.execute(
            """
            INSERT INTO data_quality_checks
            (accession, check_name, expected_value, actual_value, diff_pct, passed, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (accession, "soi_fair_value_reconciliation", target_total, computed_total, diff_pct, int(passed), now),
        )

    plain_text = build_plain_text(main_doc_path)
    non_accrual_candidates = find_non_accrual_footnote_candidates(plain_text)
    non_accrual_footnote_number = non_accrual_candidates[0] if non_accrual_candidates else None

    storage_scale = unit_multiplier / 1_000_000
    storable = investment_only

    for _, row in storable.iterrows():
        reference_rate, spread_pct = parse_reference_and_spread(row.get("Reference Rate and Spread"))
        non_accrual_flag = 0
        if non_accrual_footnote_number is not None:
            non_accrual_flag = int(footnotes_contain_number(row.get("Footnotes"), non_accrual_footnote_number))

        cost_val = to_float(row.get("Cost"))
        fair_value_val = to_float(row.get("Fair Value"))

        conn.execute(
            """
            INSERT OR REPLACE INTO portfolio_holdings
            (accession, ticker, issuer, industry, investment_type, reference_rate,
             spread_pct, interest_rate_pct, principal, cost, fair_value, non_accrual, risk_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                accession, ticker, normalize_issuer_name(row["Investments"]), row["Sector"], row["AssetClass"],
                reference_rate, spread_pct, parse_pct(row.get("Interest Rate")),
                to_float(row.get("Par Amount/Units")),
                cost_val * storage_scale if cost_val is not None else None,
                fair_value_val * storage_scale if fair_value_val is not None else None,
                non_accrual_flag, None,
            ),
        )
    conn.commit()

    return {
        "accession": accession,
        "period_end": period_end,
        "status": "ok",
        "n_holdings": len(storable),
        "page_indices": page_indices,
        "computed_total": computed_total,
        "target_total": target_total,
        "diff_pct": diff_pct,
        "passed": passed,
        "non_accrual_candidates": non_accrual_candidates,
        "non_accrual_footnote_number": non_accrual_footnote_number,
    }
