import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.schema import init_db


def run():
    conn = init_db(db_path=":memory:")

    conn.execute(
        "INSERT INTO filings (accession, ticker, cik, form_type, filing_date, period_end, fetched_at) "
        "VALUES ('acc1', 'ARCC', '1', '10-Q', '2026-01-01', '2026-03-31', 'x')"
    )

    conn.execute(
        "INSERT INTO portfolio_holdings (accession, ticker, issuer, cost, fair_value) "
        "VALUES ('acc1', 'ARCC', 'Old Name Corp (13)', 100, 100)"
    )
    conn.commit()

    total_before = conn.execute(
        "SELECT SUM(fair_value) FROM portfolio_holdings WHERE accession='acc1'"
    ).fetchone()[0]
    assert total_before == 100

    conn.execute("DELETE FROM portfolio_holdings WHERE accession = ?", ("acc1",))
    conn.execute(
        "INSERT INTO portfolio_holdings (accession, ticker, issuer, cost, fair_value) "
        "VALUES ('acc1', 'ARCC', 'Old Name Corp', 100, 100)"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT issuer, fair_value FROM portfolio_holdings WHERE accession='acc1'"
    ).fetchall()

    assert len(rows) == 1, f"expected 1 row after re-run, got {len(rows)}: {rows}"
    assert rows[0][0] == "Old Name Corp"

    total_after = conn.execute(
        "SELECT SUM(fair_value) FROM portfolio_holdings WHERE accession='acc1'"
    ).fetchone()[0]
    assert total_after == 100, f"expected 100 (not doubled to 200), got {total_after}"

    print("PASS")


if __name__ == "__main__":
    run()
