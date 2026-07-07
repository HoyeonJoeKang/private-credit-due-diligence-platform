import pandas as pd

MARKDOWN_THRESHOLD = 80.0
CONCENTRATION_THRESHOLD = 15.0

BUCKET_BOUNDS = [(0, 2, "Green"), (3, 5, "Yellow"), (6, 8, "Orange"), (9, 999, "Red")]


def bucket_for_score(score: int) -> str:
    for low, high, label in BUCKET_BOUNDS:
        if low <= score <= high:
            return label
    return "Red"


def build_issuer_quarterly_summary(holdings: pd.DataFrame) -> pd.DataFrame:
    grouped = holdings.groupby(["period_end", "issuer"]).agg(
        sector=("industry", "first"),
        cost=("cost", "sum"),
        fair_value=("fair_value", "sum"),
        non_accrual=("non_accrual", "max"),
    ).reset_index()
    grouped["fv_cost_ratio"] = grouped["fair_value"] / grouped["cost"] * 100
    return grouped


def add_sector_concentration(summary: pd.DataFrame) -> pd.DataFrame:
    summary = summary.copy()
    period_totals = summary.groupby("period_end")["fair_value"].transform("sum")
    sector_totals = summary.groupby(["period_end", "sector"])["fair_value"].transform("sum")
    summary["sector_pct_of_portfolio"] = sector_totals / period_totals * 100
    return summary


def add_prior_quarter_data(summary: pd.DataFrame) -> pd.DataFrame:
    summary = summary.sort_values(["issuer", "period_end"]).copy()
    summary["prior_fv_cost_ratio"] = summary.groupby("issuer")["fv_cost_ratio"].shift(1)
    summary["prior_non_accrual"] = summary.groupby("issuer")["non_accrual"].shift(1)
    return summary


def _score_row(row, markdown_threshold, concentration_threshold):
    score = 0
    reasons = []

    if row["non_accrual"] == 1:
        score += 3
        reasons.append("non_accrual (+3)")
        if pd.notna(row["prior_non_accrual"]) and row["prior_non_accrual"] == 0:
            score += 1
            reasons.append("newly_non_accrual (+1)")

    if row["fv_cost_ratio"] < markdown_threshold:
        score += 2
        reasons.append("fair_value_below_80pct_cost (+2)")

    if (pd.notna(row["prior_fv_cost_ratio"])
            and row["fv_cost_ratio"] < row["prior_fv_cost_ratio"]
            and row["prior_fv_cost_ratio"] < 100):
        score += 2
        reasons.append("markdown_deteriorating_2q (+2)")

    if row["sector_pct_of_portfolio"] > concentration_threshold:
        score += 1
        reasons.append("high_sector_concentration (+1)")

    return pd.Series({
        "watchlist_score": score,
        "watchlist_bucket": bucket_for_score(score),
        "watchlist_reasons": "; ".join(reasons) if reasons else "none",
    })


def compute_watchlist_scores(holdings: pd.DataFrame,
                              markdown_threshold: float = MARKDOWN_THRESHOLD,
                              concentration_threshold: float = CONCENTRATION_THRESHOLD) -> pd.DataFrame:
    summary = build_issuer_quarterly_summary(holdings)
    summary = add_sector_concentration(summary)
    summary = add_prior_quarter_data(summary)

    scores = summary.apply(
        lambda row: _score_row(row, markdown_threshold, concentration_threshold), axis=1
    )
    return pd.concat([summary, scores], axis=1)
