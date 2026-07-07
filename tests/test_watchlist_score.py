import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.watchlist_score import compute_watchlist_scores


def build_holdings():
    rows = [
        ("2025-12-31", "Issuer A", "Sector1", 100, 100, 0),
        ("2026-03-31", "Issuer A", "Sector1", 100, 95, 1),

        ("2025-12-31", "Issuer B", "Sector2", 100, 90, 0),
        ("2026-03-31", "Issuer B", "Sector2", 100, 75, 0),

        ("2025-12-31", "Issuer C", "Sector3", 50, 50, 0),
        ("2026-03-31", "Issuer C", "Sector3", 50, 50, 0),

        ("2025-12-31", "Issuer D", "Sector4", 300, 300, 0),
        ("2026-03-31", "Issuer D", "Sector4", 300, 300, 0),

        ("2025-12-31", "Issuer E", "Sector5", 200, 200, 0),
        ("2026-03-31", "Issuer E", "Sector5", 200, 200, 0),
    ]
    return pd.DataFrame(rows, columns=["period_end", "issuer", "industry", "cost", "fair_value", "non_accrual"])


def run():
    holdings = build_holdings()
    scores = compute_watchlist_scores(holdings)
    current = scores[scores["period_end"] == "2026-03-31"].set_index("issuer")

    print(current[["fv_cost_ratio", "prior_fv_cost_ratio", "sector_pct_of_portfolio",
                    "watchlist_score", "watchlist_bucket", "watchlist_reasons"]])

    total_current = 95 + 75 + 50 + 300 + 200
    sector1_pct = 95 / total_current * 100
    sector2_pct = 75 / total_current * 100
    assert sector1_pct < 15.0
    assert sector2_pct < 15.0

    assert current.loc["Issuer A", "watchlist_score"] == 4
    assert current.loc["Issuer A", "watchlist_bucket"] == "Yellow"
    assert "newly_non_accrual" in current.loc["Issuer A", "watchlist_reasons"]
    assert "high_sector_concentration" not in current.loc["Issuer A", "watchlist_reasons"]

    assert current.loc["Issuer B", "watchlist_score"] == 4
    assert "fair_value_below_80pct_cost" in current.loc["Issuer B", "watchlist_reasons"]
    assert "markdown_deteriorating_2q" in current.loc["Issuer B", "watchlist_reasons"]

    assert current.loc["Issuer C", "watchlist_score"] == 0
    assert current.loc["Issuer C", "watchlist_bucket"] == "Green"

    sector4_pct = 300 / total_current * 100
    assert sector4_pct > 15.0
    assert current.loc["Issuer D", "watchlist_score"] == 1
    assert "high_sector_concentration" in current.loc["Issuer D", "watchlist_reasons"]
    assert current.loc["Issuer D", "watchlist_bucket"] == "Green"

    print("PASS")


if __name__ == "__main__":
    run()
