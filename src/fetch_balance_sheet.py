from datetime import datetime
from pathlib import Path

import pandas as pd

from src.sec_client import fetch_text, filing_summary_url, archive_base_url
from src.filing_summary import parse_filing_summary, find_balance_sheet_reports
from src.balance_sheet import extract_total_investments_fair_value, extract_line_item, detect_unit_multiplier


def _parse_column_date(col: str):
    col = col.strip()
    for fmt in ("%b. %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(col, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _get_balance_sheet_table(ticker: str, cik: str, accession: str, raw_dir: str = "raw") -> pd.DataFrame | None:
    accession_nodash = accession.replace("-", "")
    base_dir = Path(raw_dir) / ticker / accession_nodash
    base_dir.mkdir(parents=True, exist_ok=True)

    summary_cache = base_dir / "FilingSummary.xml"
    summary_xml = fetch_text(filing_summary_url(cik, accession_nodash), cache_path=str(summary_cache))

    reports = parse_filing_summary(summary_xml)
    bs_reports = find_balance_sheet_reports(reports)
    if not bs_reports:
        return None

    html_file = bs_reports[0]["html_file"]
    cache_path = base_dir / html_file
    base_url = archive_base_url(cik, accession_nodash)
    fetch_text(f"{base_url}{html_file}", cache_path=str(cache_path))

    tables = pd.read_html(str(cache_path))
    return tables[0]


def get_total_investments_fair_value(ticker: str, cik: str, accession: str,
                                      period_end: str, raw_dir: str = "raw",
                                      label_candidates: tuple[str, ...] = ("fair value",)) -> float | None:
    df = _get_balance_sheet_table(ticker, cik, accession, raw_dir)
    if df is None:
        return None

    multiplier = detect_unit_multiplier(str(df.columns[0]))
    result = extract_total_investments_fair_value(df, unit_multiplier=multiplier,
                                                    label_candidates=label_candidates)

    for col, val in result.items():
        parsed_date = _parse_column_date(col)
        if parsed_date == period_end:
            return val
    return None


def get_leverage_metrics(ticker: str, cik: str, accession: str, period_end: str,
                          raw_dir: str = "raw") -> dict:
    df = _get_balance_sheet_table(ticker, cik, accession, raw_dir)
    if df is None:
        return {}

    multiplier = detect_unit_multiplier(str(df.columns[0]))

    line_items = {
        "total_debt": ("debt",),
        "cash_and_equivalents": ("cash and cash equivalent",),
        "total_assets": ("total assets",),
        "total_liabilities": ("total liabilities",),
    }

    metrics = {}
    for metric_name, prefixes in line_items.items():
        try:
            result = extract_line_item(df, label_prefixes=prefixes, unit_multiplier=multiplier)
        except ValueError:
            continue
        for col, val in result.items():
            parsed_date = _parse_column_date(col)
            if parsed_date == period_end:
                metrics[metric_name] = val

    if "total_assets" in metrics and "total_liabilities" in metrics:
        net_assets = metrics["total_assets"] - metrics["total_liabilities"]
        metrics["net_assets"] = net_assets
        if "total_debt" in metrics and net_assets:
            metrics["debt_to_equity"] = metrics["total_debt"] / net_assets

    return metrics
