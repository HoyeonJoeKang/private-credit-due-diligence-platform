from pathlib import Path

from src.sec_client import fetch_text, filing_summary_url, archive_base_url
from src.filing_summary import parse_filing_summary, find_schedule_of_investments_reports


def fetch_soi_reports(ticker: str, cik: str, accession: str, raw_dir: str = "raw") -> list[str]:
    accession_nodash = accession.replace("-", "")
    base_dir = Path(raw_dir) / ticker / accession_nodash
    base_dir.mkdir(parents=True, exist_ok=True)

    summary_cache = base_dir / "FilingSummary.xml"
    summary_xml = fetch_text(filing_summary_url(cik, accession_nodash), cache_path=str(summary_cache))

    reports = parse_filing_summary(summary_xml)
    soi_reports = find_schedule_of_investments_reports(reports)

    base_url = archive_base_url(cik, accession_nodash)
    saved_paths = []
    for r in soi_reports:
        html_file = r["html_file"]
        cache_path = base_dir / html_file
        fetch_text(f"{base_url}{html_file}", cache_path=str(cache_path))
        saved_paths.append(str(cache_path))

    return saved_paths


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from config.companies import COMPANIES

    info = COMPANIES["ARCC"]
    paths = fetch_soi_reports("ARCC", info["cik"], "0001628280-26-027688")
    for p in paths:
        print(p)
