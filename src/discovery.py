import sqlite3
from datetime import datetime, timezone

from src.sec_client import fetch_json, submissions_url


def discover_filings(ticker: str, cik_padded: str, cik: str, conn: sqlite3.Connection,
                      n_quarters: int = 8, cache_path: str | None = None) -> list[dict]:
    data = fetch_json(submissions_url(cik_padded), cache_path=cache_path)

    recent = data["filings"]["recent"]
    forms = recent["form"]
    accessions = recent["accessionNumber"]
    filing_dates = recent["filingDate"]
    report_dates = recent["reportDate"]
    primary_docs = recent["primaryDocument"]

    candidates = []
    for form, acc, fdate, rdate, pdoc in zip(forms, accessions, filing_dates, report_dates, primary_docs):
        if form in ("10-Q", "10-K"):
            candidates.append({
                "accession": acc,
                "accession_nodash": acc.replace("-", ""),
                "form_type": form,
                "filing_date": fdate,
                "period_end": rdate,
                "primary_document": pdoc,
            })

    candidates.sort(key=lambda x: x["filing_date"], reverse=True)
    selected = candidates[:n_quarters]

    now = datetime.now(timezone.utc).isoformat()
    for c in selected:
        primary_doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{c['accession_nodash']}/{c['primary_document']}"
        )
        summary_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{c['accession_nodash']}/FilingSummary.xml"
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO filings
            (accession, ticker, cik, form_type, filing_date, period_end,
             primary_doc_url, filing_summary_url, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (c["accession"], ticker, cik, c["form_type"], c["filing_date"],
             c["period_end"], primary_doc_url, summary_url, now),
        )
    conn.commit()
    return selected


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from src.schema import init_db
    from config.companies import COMPANIES

    conn = init_db()
    info = COMPANIES["ARCC"]
    results = discover_filings("ARCC", info["cik_padded"], info["cik"], conn,
                                cache_path="raw/ARCC/submissions.json")
    for r in results:
        print(r["form_type"], r["filing_date"], r["period_end"], r["accession"])
