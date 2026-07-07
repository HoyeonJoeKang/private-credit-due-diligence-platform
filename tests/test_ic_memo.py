import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ic_memo import build_findings, render_memo_template


def build_synthetic_data():
    filings = pd.DataFrame([
        {"accession": "acc1", "period_end": "2025-12-31"},
        {"accession": "acc2", "period_end": "2026-03-31"},
    ])

    holdings_rows = [
        ("2025-12-31", "Alpha Corp", "Sector1", 100, 100, 0),
        ("2026-03-31", "Alpha Corp", "Sector1", 100, 70, 1),

        ("2025-12-31", "Beta Corp", "Sector2", 100, 100, 0),
        ("2026-03-31", "Beta Corp", "Sector2", 100, 100, 0),

        ("2025-12-31", "Gamma Corp", "Sector3", 200, 200, 0),
        ("2026-03-31", "Gamma Corp", "Sector3", 200, 200, 0),

        ("2026-03-31", "Delta Corp", "Sector4", 50, 50, 0),
    ]
    holdings = pd.DataFrame(
        holdings_rows, columns=["period_end", "issuer", "industry", "cost", "fair_value", "non_accrual"]
    )

    financial_metrics = pd.DataFrame([
        {"period_end": "2025-12-31", "metric_name": "weighted_avg_grade", "value": 3.2},
        {"period_end": "2026-03-31", "metric_name": "weighted_avg_grade", "value": 3.0},
        {"period_end": "2025-12-31", "metric_name": "non_accrual_pct_fair_value_disclosed", "value": 1.0},
        {"period_end": "2026-03-31", "metric_name": "non_accrual_pct_fair_value_disclosed", "value": 1.8},
    ])

    return holdings, financial_metrics, filings


def run():
    holdings, financial_metrics, filings = build_synthetic_data()
    findings = build_findings("ARCC", holdings, financial_metrics, filings, "2026-03-31")

    assert findings["prior_period"] == "2025-12-31"
    assert findings["n_holdings"] == 4
    assert findings["new_issuers"] == ["Delta Corp"]
    assert findings["exited_issuers"] == []
    assert findings["weighted_avg_grade"] == 3.0
    assert findings["prior_weighted_avg_grade"] == 3.2
    assert findings["non_accrual_pct"] == 1.8
    assert findings["prior_non_accrual_pct"] == 1.0
    assert findings["overall_view"] == "Deteriorating"
    assert "Alpha Corp" in findings["watchlist_names"]

    memo = render_memo_template(findings)
    assert "Deteriorating" in memo
    assert "Alpha Corp" in memo
    assert "Delta Corp" in memo
    assert "deterministically" in memo

    print("PASS")
    print(memo)


if __name__ == "__main__":
    run()
