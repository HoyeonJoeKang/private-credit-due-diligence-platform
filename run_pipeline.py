import sys

import pandas as pd

from src.sec_client import set_contact_email
from src.schema import init_db
from config.companies import COMPANIES
from src.discovery import discover_filings
from src.fetch_balance_sheet import get_total_investments_fair_value
from src.pipeline_phase4 import process_filing_soi
from src.pipeline_bxsl import process_filing_soi_bxsl


def run_arcc(conn):
    ticker = "ARCC"
    info = COMPANIES[ticker]
    discover_filings(ticker, info["cik_padded"], info["cik"], conn,
                      cache_path=f"raw/{ticker}/submissions.json")
    filings_df = pd.read_sql(
        "SELECT * FROM filings WHERE ticker=? ORDER BY filing_date DESC", conn, params=(ticker,)
    )

    for _, f in filings_df.iterrows():
        target = get_total_investments_fair_value(ticker, info["cik"], f["accession"], f["period_end"])
        target_millions = target / 1_000_000 if target is not None else None
        result = process_filing_soi(ticker, info["cik"], f["accession"], f["primary_doc_url"],
                                     f["period_end"], conn, target_millions)
        print(ticker, {k: v for k, v in result.items() if k != "page_indices"})


def run_bxsl(conn):
    ticker = "BXSL"
    info = COMPANIES[ticker]
    discover_filings(ticker, info["cik_padded"], info["cik"], conn,
                      cache_path=f"raw/{ticker}/submissions.json")
    filings_df = pd.read_sql(
        "SELECT * FROM filings WHERE ticker=? ORDER BY filing_date DESC", conn, params=(ticker,)
    )

    for _, f in filings_df.iterrows():
        target = get_total_investments_fair_value(
            ticker, info["cik"], f["accession"], f["period_end"],
            label_candidates=("investments at fair value",)
        )
        result = process_filing_soi_bxsl(ticker, info["cik"], f["accession"], f["primary_doc_url"],
                                          f["period_end"], conn, target_total=target, unit_multiplier=1000.0)
        print(ticker, {k: v for k, v in result.items() if k != "page_indices"})


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: python run_pipeline.py your_email@example.com\n\n"
            "SEC requires a real contact email for every request this script makes."
        )

    contact_email = sys.argv[1]
    set_contact_email(contact_email)
    conn = init_db()

    print("Collecting ARCC...")
    run_arcc(conn)

    print("Collecting BXSL...")
    run_bxsl(conn)

    conn.close()
    print("\nDone. Run: streamlit run streamlit_app.py")


if __name__ == "__main__":
    main()
