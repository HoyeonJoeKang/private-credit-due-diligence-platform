import pandas as pd

from src.watchlist_score import compute_watchlist_scores


def _prior_period(period_options: list[str], selected: str) -> str | None:
    earlier = [p for p in period_options if p < selected]
    return max(earlier) if earlier else None


def _assess_direction(current: float | None, prior: float | None, higher_is_better: bool) -> int:
    if current is None or prior is None:
        return 0
    if current == prior:
        return 0
    improved = current > prior if higher_is_better else current < prior
    return 1 if improved else -1


def build_findings(ticker: str, holdings: pd.DataFrame, financial_metrics: pd.DataFrame,
                    filings: pd.DataFrame, selected_period: str) -> dict:
    period_options = sorted(filings["period_end"].unique())
    prior_period = _prior_period(period_options, selected_period)

    current_holdings = holdings[holdings["period_end"] == selected_period]
    prior_holdings = holdings[holdings["period_end"] == prior_period] if prior_period else pd.DataFrame()

    total_fv = current_holdings["fair_value"].sum()
    total_cost = current_holdings["cost"].sum()
    markdown_pct = (total_fv - total_cost) / total_cost * 100 if total_cost else None
    n_holdings = current_holdings["issuer"].nunique()

    def get_metric(period_end, name):
        row = financial_metrics[(financial_metrics["period_end"] == period_end)
                                 & (financial_metrics["metric_name"] == name)]
        return float(row["value"].iloc[0]) if not row.empty else None

    current_wag = get_metric(selected_period, "weighted_avg_grade")
    prior_wag = get_metric(prior_period, "weighted_avg_grade") if prior_period else None
    current_na_pct = get_metric(selected_period, "non_accrual_pct_fair_value_disclosed")
    prior_na_pct = get_metric(prior_period, "non_accrual_pct_fair_value_disclosed") if prior_period else None

    scores = compute_watchlist_scores(holdings)
    current_scores = scores[scores["period_end"] == selected_period]
    prior_scores = scores[scores["period_end"] == prior_period] if prior_period else pd.DataFrame()

    bucket_counts = current_scores["watchlist_bucket"].value_counts().to_dict()
    current_orange_red = int(bucket_counts.get("Orange", 0) + bucket_counts.get("Red", 0))
    if not prior_scores.empty:
        prior_bucket_counts = prior_scores["watchlist_bucket"].value_counts().to_dict()
        prior_orange_red = int(prior_bucket_counts.get("Orange", 0) + prior_bucket_counts.get("Red", 0))
    else:
        prior_orange_red = None

    watchlist_names = current_scores[current_scores["watchlist_bucket"].isin(["Orange", "Red"])] \
        .sort_values("watchlist_score", ascending=False)["issuer"].tolist()

    new_issuers, exited_issuers = [], []
    if prior_period:
        current_set = set(current_holdings["issuer"])
        prior_set = set(prior_holdings["issuer"])
        new_issuers = sorted(current_set - prior_set)
        exited_issuers = sorted(prior_set - current_set)

    grade_score = _assess_direction(current_wag, prior_wag, higher_is_better=True)
    na_score = _assess_direction(current_na_pct, prior_na_pct, higher_is_better=False)
    watchlist_score_direction = _assess_direction(current_orange_red, prior_orange_red, higher_is_better=False)

    total_direction = grade_score + na_score + watchlist_score_direction
    if total_direction > 0:
        overall_view = "Improving"
    elif total_direction < 0:
        overall_view = "Deteriorating"
    else:
        overall_view = "Stable"

    return {
        "ticker": ticker,
        "period_end": selected_period,
        "prior_period": prior_period,
        "total_fair_value": total_fv,
        "total_cost": total_cost,
        "markdown_pct": markdown_pct,
        "n_holdings": n_holdings,
        "weighted_avg_grade": current_wag,
        "prior_weighted_avg_grade": prior_wag,
        "non_accrual_pct": current_na_pct,
        "prior_non_accrual_pct": prior_na_pct,
        "watchlist_bucket_counts": bucket_counts,
        "current_orange_red_count": current_orange_red,
        "prior_orange_red_count": prior_orange_red,
        "watchlist_names": watchlist_names,
        "new_issuers": new_issuers,
        "exited_issuers": exited_issuers,
        "overall_view": overall_view,
    }


def render_memo_template(f: dict) -> str:
    lines = []
    lines.append(f"# Investment Committee Memo — {f['ticker']} — {f['period_end']}")
    lines.append("")
    lines.append(f"**Overall Portfolio Risk View: {f['overall_view']}**")
    lines.append("")
    lines.append("## Portfolio Snapshot")
    lines.append(f"- Total Fair Value: ${f['total_fair_value']:,.1f}M across {f['n_holdings']} portfolio companies")
    lines.append(f"- Total Amortized Cost: ${f['total_cost']:,.1f}M")
    if f["markdown_pct"] is not None:
        lines.append(f"- Fair Value vs Cost: {f['markdown_pct']:+.2f}%")
    lines.append("")

    lines.append("## Key Positives")
    positives = []
    if f["weighted_avg_grade"] is not None and f["prior_weighted_avg_grade"] is not None:
        if f["weighted_avg_grade"] > f["prior_weighted_avg_grade"]:
            positives.append(
                f"Weighted average portfolio grade improved from {f['prior_weighted_avg_grade']} "
                f"to {f['weighted_avg_grade']}"
            )
    if f["non_accrual_pct"] is not None and f["prior_non_accrual_pct"] is not None:
        if f["non_accrual_pct"] < f["prior_non_accrual_pct"]:
            positives.append(
                f"Non-accrual percentage improved from {f['prior_non_accrual_pct']}% "
                f"to {f['non_accrual_pct']}% (fair value basis)"
            )
    if f["new_issuers"]:
        n = len(f["new_issuers"])
        positives.append(f"{n} new portfolio compan{'y' if n == 1 else 'ies'} added this quarter")
    if not positives:
        positives.append("No notable positive developments identified this quarter")
    for p in positives:
        lines.append(f"- {p}")
    lines.append("")

    lines.append("## Key Concerns")
    concerns = []
    if f["weighted_avg_grade"] is not None and f["prior_weighted_avg_grade"] is not None:
        if f["weighted_avg_grade"] < f["prior_weighted_avg_grade"]:
            concerns.append(
                f"Weighted average portfolio grade declined from {f['prior_weighted_avg_grade']} "
                f"to {f['weighted_avg_grade']}"
            )
    if f["non_accrual_pct"] is not None and f["prior_non_accrual_pct"] is not None:
        if f["non_accrual_pct"] > f["prior_non_accrual_pct"]:
            concerns.append(
                f"Non-accrual percentage increased from {f['prior_non_accrual_pct']}% "
                f"to {f['non_accrual_pct']}% (fair value basis)"
            )
    if f["current_orange_red_count"]:
        n = f["current_orange_red_count"]
        concerns.append(
            f"{n} portfolio compan{'y' if n == 1 else 'ies'} flagged Orange/Red on the Watchlist"
        )
    if f["exited_issuers"]:
        n = len(f["exited_issuers"])
        concerns.append(f"{n} portfolio compan{'y' if n == 1 else 'ies'} exited this quarter")
    if not concerns:
        concerns.append("No material concerns identified this quarter")
    for c in concerns:
        lines.append(f"- {c}")
    lines.append("")

    lines.append("## Watchlist (Orange/Red)")
    if f["watchlist_names"]:
        for name in f["watchlist_names"][:15]:
            lines.append(f"- {name}")
        if len(f["watchlist_names"]) > 15:
            lines.append(f"- ...and {len(f['watchlist_names']) - 15} more")
    else:
        lines.append("- None flagged this quarter")
    lines.append("")

    lines.append("## Portfolio Activity")
    lines.append(f"**New Issuers ({len(f['new_issuers'])}):**")
    if f["new_issuers"]:
        for name in f["new_issuers"][:10]:
            lines.append(f"- {name}")
        if len(f["new_issuers"]) > 10:
            lines.append(f"- ...and {len(f['new_issuers']) - 10} more")
    else:
        lines.append("- None")
    lines.append("")
    lines.append(f"**Exited Issuers ({len(f['exited_issuers'])}):**")
    if f["exited_issuers"]:
        for name in f["exited_issuers"][:10]:
            lines.append(f"- {name}")
        if len(f["exited_issuers"]) > 10:
            lines.append(f"- ...and {len(f['exited_issuers']) - 10} more")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## Caveats")
    lines.append("- Fair values are Level 3 estimates based on manager judgment, not observable market prices")
    lines.append("- Watchlist Score is an illustrative rule-based framework intended to prioritize analyst "
                  "review, not to predict default")
    lines.append("- Line-item risk ratings are not disclosed by the manager; grade distribution reflects "
                  "portfolio-level aggregates only")
    lines.append("- New/exited issuer counts may be modestly overstated when a portfolio company's legal "
                  "entity name changes between filings (e.g., post-restructuring renames); punctuation and "
                  "separator differences are normalized, but substantive name changes are not auto-merged "
                  "to avoid incorrectly combining distinct companies")
    lines.append("- This memo is generated deterministically from calculated metrics; any language model "
                  "used downstream affects only phrasing, not the underlying figures or conclusions")

    return "\n".join(lines)
