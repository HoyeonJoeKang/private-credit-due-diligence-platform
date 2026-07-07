import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.schema import init_db
from src.discovery import discover_filings

FIXTURE_PATH = str(Path(__file__).resolve().parent / "fixtures" / "sample_submissions.json")


def run():
    conn = init_db(db_path=":memory:")
    results = discover_filings(
        ticker="ARCC",
        cik_padded="0001287750",
        cik="1287750",
        conn=conn,
        n_quarters=8,
        cache_path=FIXTURE_PATH,
    )

    assert len(results) == 8
    assert all(r["form_type"] in ("10-Q", "10-K") for r in results)
    dates = [r["filing_date"] for r in results]
    assert dates == sorted(dates, reverse=True)

    print("PASS")
    for r in results:
        print(r["form_type"], r["filing_date"], r["period_end"], r["accession"])


if __name__ == "__main__":
    run()
