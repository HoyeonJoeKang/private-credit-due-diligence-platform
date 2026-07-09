import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.schema import init_db
from src.discovery import discover_amendments

FIXTURE_PATH = str(Path(__file__).resolve().parent / "fixtures" / "sample_submissions_with_amendment.json")


def run():
    conn = init_db(db_path=":memory:")
    results = discover_amendments(
        ticker="ARCC",
        cik_padded="0001287750",
        cik="1287750",
        conn=conn,
        cache_path=FIXTURE_PATH,
    )

    assert len(results) == 2, f"expected 2 amendments, got {len(results)}"
    form_types = {r["form_type"] for r in results}
    assert form_types == {"10-Q/A", "10-K/A"}

    row_count = conn.execute("SELECT COUNT(*) FROM filing_amendments").fetchone()[0]
    assert row_count == 2

    print("PASS")
    for r in results:
        print(r["form_type"], r["filing_date"], r["period_end"], r["accession"])


if __name__ == "__main__":
    run()
