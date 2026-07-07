import re
from datetime import datetime, timezone

import pandas as pd

from src.fetch_main_doc import fetch_main_document
from src.fetch_soi_full import find_soi_page_tables, parse_all_soi_pages, to_float
from src.footnote_legend import build_plain_text, find_non_accrual_footnote_candidates, footnotes_contain_number
from src.grade_distribution import parse_grade_distribution

PCT_PATTERN = re.compile(r"(-?\d+\.?\d*)\s*%")
NAME_FOOTNOTE_SUFFIX_PATTERN = re.compile(r"\s*(\(\d+\))+\s*$")


def normalize_issuer_name(name: str) -> str:
    name = NAME_FOOTNOTE_SUFFIX_PATTERN.sub("", str(name)).strip()
    name = re.sub(r"\s+&\s+", " and ", name)
    name = re.sub(r"\s+/\s+", " and ", name)
    name = name.rstrip(".").strip()
    return name


def parse_pct(text) -> float | None:
    if text is None or pd.isna(text):
        return None
    m = PCT_PATTERN.search(str(text))
    return float(m.group(1)) if m else None


def _store_metric(conn, accession, ticker, metric_name, value, period_end):
    if value is None:
        return
    conn.execute(
        """
        INSERT OR REPLACE INTO financial_metrics
        (accession, ticker, metric_name, xbrl_tag, value, period_end)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (accession, ticker, metric_name, None, value, period_end),
    )


def _select_best_non_accrual_number(line_level: pd.DataFrame, candidates: list[int],
                                     disclosed_pct: float | None) -> tuple[int | None, dict]:
    if not candidates:
        return None, {}

    total_fv = line_level["Fair Value Num"].sum()
    scored = {}
    for n in candidates:
        flags = line_level["Footnotes"].apply(lambda f: footnotes_contain_number(f, n))
        na_fv = line_level.loc[flags, "Fair Value Num"].sum()
        pct = na_fv / total_fv * 100 if total_fv else 0
        scored[n] = pct

    if disclosed_pct is None:
        best = candidates[0]
    else:
        best = min(candidates, key=lambda n: abs(scored[n] - disclosed_pct))

    return best, scored


def process_filing_soi(ticker: str, cik: str, accession: str, primary_doc_url: str,
                        period_end: str, conn, target_total_millions: float | None) -> dict:
    main_doc_path = fetch_main_document(ticker, accession, primary_doc_url)
    all_tables = pd.read_html(main_doc_path)
    page_indices = find_soi_page_tables(all_tables)
    full_soi = parse_all_soi_pages(all_tables, page_indices)

    if full_soi.empty:
        return {"accession": accession, "status": "no_tables_found"}

    plain_text = build_plain_text(main_doc_path)
    non_accrual_candidates = find_non_accrual_footnote_candidates(plain_text)
    grade_info = parse_grade_distribution(plain_text)
    disclosed_non_accrual_fv_pct = grade_info.get("non_accrual_pct_fair_value_current")
    disclosed_non_accrual_cost_pct = grade_info.get("non_accrual_pct_cost_current")

    full_soi["Fair Value Num"] = full_soi["Fair Value"].apply(to_float)
    line_level = full_soi[full_soi["RowType"].isin(["company_row", "tranche_continuation"])]
    computed_total = line_level["Fair Value Num"].sum()

    missing_issuer = line_level["Company_Filled"].isna().sum()
    line_level = line_level[line_level["Company_Filled"].notna()].copy()

    non_accrual_footnote_number, candidate_scores = _select_best_non_accrual_number(
        line_level, non_accrual_candidates, disclosed_non_accrual_fv_pct
    )

    if non_accrual_footnote_number is not None:
        line_level["non_accrual_flag"] = line_level["Footnotes"].apply(
            lambda f: int(footnotes_contain_number(f, non_accrual_footnote_number))
        )
    else:
        line_level["non_accrual_flag"] = 0

    now = datetime.now(timezone.utc).isoformat()
    passed = None
    diff_pct = None
    if target_total_millions is not None:
        diff_pct = (computed_total - target_total_millions) / target_total_millions * 100
        passed = abs(diff_pct) < 0.01
        conn.execute(
            """
            INSERT INTO data_quality_checks
            (accession, check_name, expected_value, actual_value, diff_pct, passed, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (accession, "soi_fair_value_reconciliation", target_total_millions,
             computed_total, diff_pct, int(passed), now),
        )

    for _, row in line_level.iterrows():
        conn.execute(
            """
            INSERT OR REPLACE INTO portfolio_holdings
            (accession, ticker, issuer, industry, investment_type, reference_rate,
             spread_pct, interest_rate_pct, principal, cost, fair_value, non_accrual, risk_rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                accession, ticker, normalize_issuer_name(row["Company_Filled"]), row["Sector"], row["Investment"],
                row.get("Reference"), parse_pct(row.get("Spread")), parse_pct(row.get("Coupon")),
                to_float(row.get("Principal")), to_float(row.get("Amortized Cost")),
                to_float(row.get("Fair Value")), int(row["non_accrual_flag"]), None,
            ),
        )

    for grade, stats in grade_info.get("current", {}).items():
        _store_metric(conn, accession, ticker, f"grade_{grade}_fair_value_pct", stats["pct_fair_value"], period_end)
        _store_metric(conn, accession, ticker, f"grade_{grade}_fair_value", stats["fair_value"], period_end)
    _store_metric(conn, accession, ticker, "weighted_avg_grade",
                   grade_info.get("weighted_avg_grade_current"), period_end)
    _store_metric(conn, accession, ticker, "non_accrual_pct_fair_value_disclosed",
                   disclosed_non_accrual_fv_pct, period_end)
    _store_metric(conn, accession, ticker, "non_accrual_pct_cost_disclosed",
                   disclosed_non_accrual_cost_pct, period_end)

    non_accrual_check_passed = None
    non_accrual_diff = None
    computed_non_accrual_pct = candidate_scores.get(non_accrual_footnote_number) if non_accrual_footnote_number else None
    if disclosed_non_accrual_fv_pct is not None and computed_non_accrual_pct is not None:
        non_accrual_diff = computed_non_accrual_pct - disclosed_non_accrual_fv_pct
        non_accrual_check_passed = abs(non_accrual_diff) < 0.2
        conn.execute(
            """
            INSERT INTO data_quality_checks
            (accession, check_name, expected_value, actual_value, diff_pct, passed, checked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (accession, "non_accrual_pct_reconciliation", disclosed_non_accrual_fv_pct,
             computed_non_accrual_pct, non_accrual_diff, int(non_accrual_check_passed), now),
        )

    conn.commit()

    return {
        "accession": accession,
        "period_end": period_end,
        "status": "ok",
        "n_holdings": len(line_level),
        "missing_issuer_dropped": int(missing_issuer),
        "non_accrual_candidates": non_accrual_candidates,
        "non_accrual_footnote_number": non_accrual_footnote_number,
        "n_non_accrual": int(line_level["non_accrual_flag"].sum()),
        "non_accrual_pct_disclosed": disclosed_non_accrual_fv_pct,
        "non_accrual_check_passed": non_accrual_check_passed,
        "non_accrual_diff": non_accrual_diff,
        "computed_total": computed_total,
        "target_total": target_total_millions,
        "diff_pct": diff_pct,
        "passed": passed,
    }
