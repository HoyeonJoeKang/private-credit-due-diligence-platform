import io
import os
import sqlite3

import streamlit as st

try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError as e:
    st.error(
        f"Required library is not installed: **{e.name}**\n\n"
        f"Run the following command in your terminal, then restart this app.\n\n"
        f"```\npip install -r requirements.txt\n```"
    )
    st.stop()

try:
    from src.watchlist_score import compute_watchlist_scores
except ImportError as e:
    st.error(
        f"Could not load project code ({e.name}). "
        f"Make sure streamlit_app.py is being run from the project folder "
        f"(the one containing src/, config/, etc.)."
    )
    st.stop()

NAVY = "#12233F"
STEEL = "#2E4A6B"
ACCENT = "#3E8ED0"
GRAY = "#7A8699"
BG = "#F4F6F9"
RED = "#C0392B"
GREEN = "#1E8F5F"
YELLOW = "#D4A017"
ORANGE = "#D9791E"

PALETTE = [NAVY, ACCENT, STEEL, "#6C8FBF", "#9FB6D9", GRAY, "#5A7A9A", "#B8C4D4", "#D6DEE8"]
BUCKET_COLORS = {"Green": GREEN, "Yellow": YELLOW, "Orange": ORANGE, "Red": RED}


def categorize_investment_type(text):
    if text is None or pd.isna(text):
        return "Unclassified"
    t = str(text).lower()
    if "first lien" in t:
        return "First Lien"
    if "second lien" in t:
        return "Second Lien"
    if "subordinated" in t or "mezzanine" in t:
        return "Subordinated"
    if "equity" in t or "membership" in t or "partnership" in t or "units" in t or "warrant" in t or "preferred" in t:
        return "Equity / Other Ownership"
    if "unsecured" in t:
        return "Unsecured Debt"
    return "Other"


def group_small_slices(df: pd.DataFrame, label_col: str, value_col: str, top_n: int = 8) -> pd.DataFrame:
    df = df.sort_values(value_col, ascending=False).reset_index(drop=True)
    if len(df) <= top_n:
        return df
    top = df.iloc[:top_n].copy()
    other_sum = df.iloc[top_n:][value_col].sum()
    other_row = pd.DataFrame({label_col: ["Other"], value_col: [other_sum]})
    return pd.concat([top, other_row], ignore_index=True)


def to_quarter_label(period_end: str) -> str:
    year, month, _ = period_end.split("-")
    quarter = (int(month) - 1) // 3 + 1
    return f"{year} Q{quarter}"


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()


def download_button(df: pd.DataFrame, label: str, filename: str, key: str):
    st.download_button(
        label=label,
        data=to_excel_bytes(df),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
    )


@st.cache_data
def load_data(db_path: str):
    conn = sqlite3.connect(db_path)
    filings = pd.read_sql("SELECT * FROM filings ORDER BY period_end", conn)
    holdings = pd.read_sql("SELECT * FROM portfolio_holdings", conn)
    quality = pd.read_sql("SELECT * FROM data_quality_checks", conn)
    financial_metrics = pd.read_sql("SELECT * FROM financial_metrics", conn)
    try:
        amendments = pd.read_sql("SELECT * FROM filing_amendments ORDER BY filing_date", conn)
    except Exception:
        amendments = pd.DataFrame(columns=["accession", "ticker", "cik", "form_type",
                                            "filing_date", "period_end", "primary_doc_url"])
    conn.close()
    holdings = holdings.merge(filings[["accession", "period_end"]], on="accession", how="left")
    holdings["investment_category"] = holdings["investment_type"].apply(categorize_investment_type)
    return filings, holdings, quality, amendments, financial_metrics


st.set_page_config(page_title="Private Credit Due Diligence Platform", layout="wide")

st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; }}
.metric-card {{
    background-color: white;
    border-radius: 10px;
    padding: 18px 20px;
    border: 1px solid #E1E6ED;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.metric-label {{ color: {GRAY}; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; }}
.metric-value {{ color: {NAVY}; font-size: 28px; font-weight: 700; margin-top: 4px; }}
.section-header {{ color: {NAVY}; font-size: 20px; font-weight: 700; margin-top: 8px; }}
.pass-badge {{ background-color: {GREEN}; color: white; padding: 3px 10px; border-radius: 6px; font-size: 13px; }}
.fail-badge {{ background-color: {RED}; color: white; padding: 3px 10px; border-radius: 6px; font-size: 13px; }}
.concern-card {{
    border-left: 4px solid {GRAY};
    padding: 10px 14px;
    margin-bottom: 8px;
    background-color: white;
    border-radius: 4px;
}}
.concern-title {{ font-weight: 700; color: {NAVY}; }}
.concern-reason {{ color: {GRAY}; font-size: 13px; }}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"<div style='color:{NAVY}; font-size:20px; font-weight:700;'>Private Credit Due Diligence Platform</div>", unsafe_allow_html=True)

default_folder = st.session_state.get("folder_path", os.getcwd())
folder_path = st.sidebar.text_input(
    "Project folder path",
    value=default_folder,
    help="Defaults to the folder this app was launched from. Change only if your data lives elsewhere.",
)
st.session_state["folder_path"] = folder_path

if not folder_path:
    st.info("Paste the project folder path into the sidebar to get started.")
    st.stop()

db_path = os.path.join(folder_path, "parsed", "dd_platform.db")
if not os.path.exists(db_path):
    st.error(
        f"No data found at: {db_path}\n\n"
        f"This looks like the first time running this project. Before using this dashboard, "
        f"you need to collect the data once:\n\n"
        f"1. Open a terminal in this project folder\n"
        f"2. Edit run_pipeline.py and set your email in CONTACT_EMAIL\n"
        f"3. Run: python run_pipeline.py\n"
        f"4. Wait for it to finish (it fetches real filings from SEC, can take a while)\n"
        f"5. Come back here and refresh this page"
    )
    st.stop()

filings, holdings, quality, amendments, financial_metrics = load_data(db_path)

if filings.empty:
    st.warning("The filings table is empty. Please run the data collection pipeline first.")
    st.stop()

tickers = sorted(filings["ticker"].unique())
selected_ticker = st.sidebar.selectbox("Company", tickers)

filings = filings[filings["ticker"] == selected_ticker].copy()
holdings = holdings[holdings["ticker"] == selected_ticker].copy()
quality = quality[quality["accession"].isin(filings["accession"])].copy()
amendments = amendments[amendments["ticker"] == selected_ticker].copy() if not amendments.empty else amendments
financial_metrics = financial_metrics[financial_metrics["ticker"] == selected_ticker].copy()

st.sidebar.caption(f"{len(filings)} quarters loaded for {selected_ticker}")
page = st.sidebar.radio("Section", ["Overview", "Composition", "Risk & Changes", "Watchlist", "Data Quality"])

period_options = sorted(filings["period_end"].unique(), reverse=True)
selected_period = period_options[0]

current_holdings = holdings[holdings["period_end"] == selected_period].copy()
prior_periods = [p for p in period_options if p < selected_period]
prior_period = prior_periods[0] if prior_periods else None
prior_holdings = holdings[holdings["period_end"] == prior_period].copy() if prior_period else pd.DataFrame()

trend = (
    holdings.groupby("period_end")
    .agg(total_fair_value=("fair_value", "sum"), total_cost=("cost", "sum"))
    .reset_index()
    .sort_values("period_end")
)

st.markdown(f"<div class='section-header'>{selected_ticker} — Private Credit Due Diligence Platform</div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='color:{STEEL}; font-size:15px; font-weight:600; margin-top:-6px;'>"
    f"Most Recent Data: {to_quarter_label(selected_period)}</div>",
    unsafe_allow_html=True,
)
st.caption(f"Latest filing period: {selected_period}. Built on public SEC filings. Not investment advice.")

if page == "Overview":
    total_fv = current_holdings["fair_value"].sum()
    total_cost = current_holdings["cost"].sum()
    n_holdings = current_holdings["issuer"].nunique()
    overall_markdown = (total_fv - total_cost) / total_cost * 100 if total_cost else None

    c1, c2, c3, c4 = st.columns(4)
    for col, label, value in zip(
        [c1, c2, c3, c4],
        ["Total Fair Value ($M)", "Total Cost ($M)", "Portfolio Companies", "Fair Value vs Cost"],
        [f"{total_fv:,.1f}", f"{total_cost:,.1f}", f"{n_holdings}",
         f"{overall_markdown:+.2f}%" if overall_markdown is not None else "N/A"],
    ):
        col.markdown(
            f"<div class='metric-card'><div class='metric-label'>{label}</div>"
            f"<div class='metric-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    current_accession = current_holdings["accession"].iloc[0] if not current_holdings.empty else None
    check_row = quality[(quality["accession"] == current_accession)
                         & (quality["check_name"] == "soi_fair_value_reconciliation")]
    if not check_row.empty:
        row = check_row.iloc[0]
        badge_class = "pass-badge" if row["passed"] else "fail-badge"
        badge_text = "RECONCILED" if row["passed"] else "MISMATCH"
        st.markdown(
            f"Data quality vs Balance Sheet: <span class='{badge_class}'>{badge_text}</span> "
            f"(diff {row['diff_pct']:.4f}%)",
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("<div class='section-header'>Portfolio Trend</div>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["period_end"], y=trend["total_fair_value"],
                              name="Fair Value", line=dict(color=NAVY, width=3)))
    fig.add_trace(go.Scatter(x=trend["period_end"], y=trend["total_cost"],
                              name="Amortized Cost", line=dict(color=ACCENT, width=3, dash="dot")))
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=380,
                       margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, width='stretch')

    leverage_current = financial_metrics[
        (financial_metrics["accession"] == current_accession)
        & (financial_metrics["metric_name"].isin(
            ["total_debt", "net_assets", "debt_to_equity", "cash_and_equivalents"]))
    ].set_index("metric_name")["value"]

    if not leverage_current.empty:
        st.write("")
        st.markdown("<div class='section-header'>Leverage &amp; Liquidity</div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        total_debt = leverage_current.get("total_debt")
        net_assets = leverage_current.get("net_assets")
        debt_to_equity = leverage_current.get("debt_to_equity")
        cash = leverage_current.get("cash_and_equivalents")
        for col, label, value in zip(
            [c1, c2, c3, c4],
            ["Total Debt ($M)", "Net Assets / NAV ($M)", "Debt / Equity", "Cash & Equivalents ($M)"],
            [f"{total_debt/1_000_000:,.1f}" if total_debt is not None else "N/A",
             f"{net_assets/1_000_000:,.1f}" if net_assets is not None else "N/A",
             f"{debt_to_equity:.2f}x" if debt_to_equity is not None else "N/A",
             f"{cash/1_000_000:,.1f}" if cash is not None else "N/A"],
        ):
            col.markdown(
                f"<div class='metric-card'><div class='metric-label'>{label}</div>"
                f"<div class='metric-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )

        leverage_trend = financial_metrics[
            financial_metrics["metric_name"] == "debt_to_equity"
        ].sort_values("period_end")
        if not leverage_trend.empty:
            st.write("")
            fig = px.line(leverage_trend, x="period_end", y="value", markers=True,
                          color_discrete_sequence=[STEEL])
            fig.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Debt / Equity")
            st.plotly_chart(fig, width='stretch')

        debt_vs_equity = financial_metrics[
            financial_metrics["metric_name"].isin(["total_debt", "net_assets"])
        ].pivot_table(index="period_end", columns="metric_name", values="value").reset_index().sort_values("period_end")
        cash_trend = financial_metrics[
            financial_metrics["metric_name"] == "cash_and_equivalents"
        ].sort_values("period_end")

        col_a, col_b = st.columns(2)
        with col_a:
            if not debt_vs_equity.empty:
                st.markdown("<div class='section-header' style='font-size:15px;'>Total Debt vs Net Assets</div>",
                            unsafe_allow_html=True)
                fig = go.Figure()
                if "total_debt" in debt_vs_equity.columns:
                    fig.add_trace(go.Scatter(x=debt_vs_equity["period_end"], y=debt_vs_equity["total_debt"],
                                              name="Total Debt", line=dict(color=NAVY, width=3)))
                if "net_assets" in debt_vs_equity.columns:
                    fig.add_trace(go.Scatter(x=debt_vs_equity["period_end"], y=debt_vs_equity["net_assets"],
                                              name="Net Assets", line=dict(color=ACCENT, width=3, dash="dot")))
                fig.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                  margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.15))
                st.plotly_chart(fig, width='stretch')
        with col_b:
            if not cash_trend.empty:
                st.markdown("<div class='section-header' style='font-size:15px;'>Cash &amp; Equivalents</div>",
                            unsafe_allow_html=True)
                fig = px.line(cash_trend, x="period_end", y="value", markers=True,
                              color_discrete_sequence=[GREEN])
                fig.update_layout(height=280, plot_bgcolor="white", paper_bgcolor="white",
                                  margin=dict(l=10, r=10, t=10, b=10), yaxis_title="$")
                st.plotly_chart(fig, width='stretch')

elif page == "Composition":
    col1, col2 = st.columns(2)

    sector_summary_full = (
        current_holdings.groupby("industry")["fair_value"].sum()
        .sort_values(ascending=False).reset_index()
    )

    with col1:
        st.markdown("<div class='section-header'>Sector Composition</div>", unsafe_allow_html=True)
        sector_summary = group_small_slices(sector_summary_full, "industry", "fair_value")
        fig = px.pie(sector_summary, names="industry", values="fair_value", hole=0.45,
                     color_discrete_sequence=PALETTE)
        fig.update_traces(textinfo="percent", textposition="inside")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                           legend=dict(orientation="v"))
        st.plotly_chart(fig, width='stretch')

    type_summary_full = (
        current_holdings.groupby("investment_category")["fair_value"].sum()
        .sort_values(ascending=False).reset_index()
    )

    with col2:
        st.markdown("<div class='section-header'>Investment Type</div>", unsafe_allow_html=True)
        type_summary = group_small_slices(type_summary_full, "investment_category", "fair_value")
        fig = px.pie(type_summary, names="investment_category", values="fair_value", hole=0.45,
                     color_discrete_sequence=PALETTE)
        fig.update_traces(textinfo="percent", textposition="inside")
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width='stretch')

    download_button(sector_summary_full, "Download sector composition (Excel)",
                     f"{selected_ticker}_sector_composition_{selected_period}.xlsx", "dl_sector")

    st.markdown("<div class='section-header'>Top 15 Holdings & Concentration</div>", unsafe_allow_html=True)
    issuer_summary = (
        current_holdings.groupby("issuer")["fair_value"].sum()
        .sort_values(ascending=False).reset_index()
    )
    total_fv = issuer_summary["fair_value"].sum()
    top10_pct = issuer_summary.head(10)["fair_value"].sum() / total_fv * 100 if total_fv else 0
    st.markdown(f"Top 10 issuer concentration: **{top10_pct:.1f}%** of total portfolio fair value")

    top15 = issuer_summary.head(15)
    fig = px.bar(top15, x="fair_value", y="issuer", orientation="h",
                 color_discrete_sequence=[NAVY])
    fig.update_layout(yaxis=dict(autorange="reversed"), height=460, plot_bgcolor="white",
                       paper_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_title="Fair Value ($M)", yaxis_title="")
    st.plotly_chart(fig, width='stretch')

    download_button(issuer_summary, "Download all holdings (Excel)",
                     f"{selected_ticker}_holdings_{selected_period}.xlsx", "dl_holdings")

elif page == "Risk & Changes":
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<div class='section-header'>Interest Rate Exposure</div>", unsafe_allow_html=True)
        rated = current_holdings[current_holdings["interest_rate_pct"].notna()].copy()
        if not rated.empty:
            rated["rate_type"] = rated["reference_rate"].apply(
                lambda x: "Floating" if pd.notna(x) and str(x).strip() != "" else "Fixed"
            )
            rate_summary = rated.groupby("rate_type")["fair_value"].sum().reset_index()
            fig = px.pie(rate_summary, names="rate_type", values="fair_value", hole=0.45,
                         color_discrete_sequence=[NAVY, ACCENT])
            fig.update_traces(textinfo="percent", textposition="inside")
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, width='stretch')

            weighted_avg = (rated["interest_rate_pct"] * rated["fair_value"]).sum() / rated["fair_value"].sum()
            st.markdown(f"Weighted average coupon: **{weighted_avg:.2f}%**")
        else:
            st.write("No rate data available for this quarter")

    with col2:
        st.markdown("<div class='section-header'>New vs Exited Issuers</div>", unsafe_allow_html=True)
        new_issuers, exited_issuers = set(), set()
        if prior_period:
            current_issuers = set(current_holdings["issuer"])
            prior_issuers = set(prior_holdings["issuer"])
            new_issuers = current_issuers - prior_issuers
            exited_issuers = prior_issuers - current_issuers
            st.metric("New Issuers", len(new_issuers))
            st.metric("Exited Issuers", len(exited_issuers))
        else:
            st.write("No prior quarter available for comparison")

    with col3:
        st.markdown("<div class='section-header'>Non-Accrual Tracker</div>", unsafe_allow_html=True)
        total_fv = current_holdings["fair_value"].sum()
        non_accrual_holdings = current_holdings[current_holdings["non_accrual"] == 1]
        non_accrual_fv = non_accrual_holdings["fair_value"].sum()
        non_accrual_pct = non_accrual_fv / total_fv * 100 if total_fv else 0
        st.metric("Non-Accrual (% of Fair Value)", f"{non_accrual_pct:.2f}%")
        st.metric("Non-Accrual Issuers", non_accrual_holdings["issuer"].nunique())

    if prior_period:
        st.markdown(f"<div class='section-header'>New Issuers ({selected_period} vs {prior_period})</div>", unsafe_allow_html=True)
        new_df = (
            current_holdings[current_holdings["issuer"].isin(new_issuers)]
            .groupby("issuer")["fair_value"].sum().sort_values(ascending=False).reset_index()
        )
        st.dataframe(new_df, width='stretch')

        st.markdown("<div class='section-header'>Exited Issuers</div>", unsafe_allow_html=True)
        exited_df = (
            prior_holdings[prior_holdings["issuer"].isin(exited_issuers)]
            .groupby("issuer")["fair_value"].sum().sort_values(ascending=False).reset_index()
        )
        st.dataframe(exited_df, width='stretch')

        new_labeled = new_df.copy()
        new_labeled["Status"] = "New"
        exited_labeled = exited_df.copy()
        exited_labeled["Status"] = "Exited"
        combined_changes = pd.concat([new_labeled, exited_labeled], ignore_index=True)
        download_button(combined_changes, "Download new & exited issuers (Excel)",
                         f"{selected_ticker}_new_and_exited_{selected_period}.xlsx", "dl_changes")

    st.markdown("<div class='section-header'>Largest Fair Value Markdowns</div>", unsafe_allow_html=True)
    markdown_ranked = (
        current_holdings.groupby("issuer")
        .agg(cost=("cost", "sum"), fair_value=("fair_value", "sum"))
        .reset_index()
    )
    markdown_ranked["markdown_pct"] = (
        (markdown_ranked["fair_value"] - markdown_ranked["cost"]) / markdown_ranked["cost"] * 100
    )
    markdown_ranked = markdown_ranked.sort_values("markdown_pct")
    fig_data = markdown_ranked.head(15)
    fig = px.bar(fig_data, x="markdown_pct", y="issuer", orientation="h",
                 color="markdown_pct", color_continuous_scale=[RED, GRAY, GREEN])
    fig.update_layout(yaxis=dict(autorange="reversed"), height=460, plot_bgcolor="white",
                       paper_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_title="Fair Value vs Cost (%)", yaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig, width='stretch')

    download_button(markdown_ranked, "Download markdown ranking (Excel)",
                     f"{selected_ticker}_markdown_ranking_{selected_period}.xlsx", "dl_markdown")

    st.markdown("<div class='section-header'>Non-Accrual Holdings (Current Quarter)</div>", unsafe_allow_html=True)
    non_accrual_detail = (
        current_holdings[current_holdings["non_accrual"] == 1]
        .groupby("issuer")
        .agg(industry=("industry", "first"), cost=("cost", "sum"), fair_value=("fair_value", "sum"))
        .reset_index()
        .sort_values("fair_value", ascending=False)
    )
    if non_accrual_detail.empty:
        st.write("No non-accrual holdings this quarter")
    else:
        st.dataframe(non_accrual_detail, width='stretch')
        download_button(non_accrual_detail, "Download non-accrual holdings (Excel)",
                         f"{selected_ticker}_non_accrual_{selected_period}.xlsx", "dl_nonaccrual")

    non_accrual_trend = (
        holdings.groupby("period_end")
        .apply(lambda g: g[g["non_accrual"] == 1]["fair_value"].sum() / g["fair_value"].sum() * 100
               if g["fair_value"].sum() else 0, include_groups=False)
        .reset_index(name="non_accrual_pct")
        .sort_values("period_end")
    )
    st.markdown("<div class='section-header'>Non-Accrual Trend</div>", unsafe_allow_html=True)
    fig = px.line(non_accrual_trend, x="period_end", y="non_accrual_pct", markers=True,
                  color_discrete_sequence=[RED])
    fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                       margin=dict(l=10, r=10, t=10, b=10), yaxis_title="% of Fair Value")
    st.plotly_chart(fig, width='stretch')

    if "pik_rate" in holdings.columns:
        pik_trend = (
            holdings.groupby("period_end")
            .apply(lambda g: g[g["pik_rate"].notna()]["fair_value"].sum() / g["fair_value"].sum() * 100
                   if g["fair_value"].sum() else 0, include_groups=False)
            .reset_index(name="pik_pct")
            .sort_values("period_end")
        )
        st.markdown("<div class='section-header'>PIK Income Trend</div>", unsafe_allow_html=True)
        st.caption("Share of portfolio fair value earning payment-in-kind interest, by quarter")
        fig = px.line(pik_trend, x="period_end", y="pik_pct", markers=True,
                      color_discrete_sequence=[ORANGE])
        fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                           margin=dict(l=10, r=10, t=10, b=10), yaxis_title="% of Fair Value")
        st.plotly_chart(fig, width='stretch')

        current_pik = current_holdings[current_holdings["pik_rate"].notna()]
        if not current_pik.empty:
            weighted_pik = (current_pik["pik_rate"] * current_pik["fair_value"]).sum() / current_pik["fair_value"].sum()
            st.markdown(f"Weighted average PIK rate this quarter: **{weighted_pik:.2f}%**")


elif page == "Watchlist":
    all_scores = compute_watchlist_scores(holdings)
    current_scores = all_scores[all_scores["period_end"] == selected_period].copy()
    current_scores = current_scores.sort_values("watchlist_score", ascending=False)

    st.caption(
        "This is an illustrative rule-based early warning framework. Thresholds are intended "
        "to prioritize analyst review, not to predict default."
    )

    bucket_counts = current_scores["watchlist_bucket"].value_counts()

    cols = st.columns(4)
    for col, bucket in zip(cols, ["Green", "Yellow", "Orange", "Red"]):
        count = int(bucket_counts.get(bucket, 0))
        col.markdown(
            f"<div class='metric-card' style='border-top: 4px solid {BUCKET_COLORS[bucket]};'>"
            f"<div class='metric-label'>{bucket}</div>"
            f"<div class='metric-value'>{count}</div></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    top_concern = current_scores[current_scores["watchlist_bucket"].isin(["Orange", "Red"])].head(10)
    if not top_concern.empty:
        st.markdown("<div class='section-header'>Top Concerns</div>", unsafe_allow_html=True)
        for _, r in top_concern.iterrows():
            color = BUCKET_COLORS.get(r["watchlist_bucket"], GRAY)
            st.markdown(
                f"<div class='concern-card' style='border-left-color:{color};'>"
                f"<span class='concern-title'>{r['issuer']}</span> "
                f"&mdash; Score {int(r['watchlist_score'])} ({r['watchlist_bucket']})<br>"
                f"<span class='concern-reason'>{r['watchlist_reasons']}</span></div>",
                unsafe_allow_html=True,
            )
        st.write("")

    st.markdown("<div class='section-header'>Score Distribution</div>", unsafe_allow_html=True)
    dist_data = current_scores.sort_values("watchlist_score", ascending=False).head(30)
    fig = px.bar(dist_data, x="watchlist_score", y="issuer", orientation="h",
                 color="watchlist_bucket", color_discrete_map=BUCKET_COLORS)
    fig.update_layout(yaxis=dict(autorange="reversed"), height=600, plot_bgcolor="white",
                       paper_bgcolor="white", margin=dict(l=10, r=10, t=10, b=10),
                       xaxis_title="Watchlist Score", yaxis_title="", legend_title="")
    st.plotly_chart(fig, width='stretch')

    st.markdown("<div class='section-header'>Full Watchlist Detail</div>", unsafe_allow_html=True)

    def highlight_bucket(row):
        color = BUCKET_COLORS.get(row["watchlist_bucket"], "white")
        return [f"background-color: {color}22"] * len(row)

    display_cols = [
        "issuer", "sector", "fv_cost_ratio", "sector_pct_of_portfolio",
        "watchlist_score", "watchlist_bucket", "watchlist_reasons",
    ]
    styled = current_scores[display_cols].style.apply(highlight_bucket, axis=1).format({
        "fv_cost_ratio": "{:.1f}%",
        "sector_pct_of_portfolio": "{:.1f}%",
    })
    st.dataframe(styled, width='stretch', height=500)

    download_button(current_scores[display_cols], "Download watchlist (Excel)",
                     f"{selected_ticker}_watchlist_{selected_period}.xlsx", "dl_watchlist")

elif page == "Data Quality":
    st.caption(
        "This tab shows whether the figures this platform parsed from SEC filings match the "
        "official numbers reported in each quarter's filing (reconciliation), and how complete "
        "certain data fields are for the current quarter."
    )

    st.markdown("<div class='section-header'>Reconciliation History</div>", unsafe_allow_html=True)
    st.caption(
        "Each row compares a figure this platform calculated from parsed filing data (Actual Value) "
        "against the official figure reported elsewhere in the same filing (Expected Value). "
        "A small Difference (%) and Passed = True means our parsing is accurate for that quarter."
    )
    quality_display = quality.merge(
        filings[["accession", "period_end"]], on="accession", how="left"
    ).sort_values("period_end")
    quality_display = quality_display.rename(columns={
        "check_name": "Check",
        "expected_value": "Expected Value",
        "actual_value": "Actual Value",
        "diff_pct": "Difference (%)",
        "passed": "Passed",
        "period_end": "Quarter",
    })
    display_order = ["Quarter", "Check", "Expected Value", "Actual Value", "Difference (%)", "Passed"]
    st.dataframe(quality_display[display_order], width='stretch')
    download_button(quality_display[display_order], "Download reconciliation history (Excel)",
                     f"{selected_ticker}_reconciliation_history.xlsx", "dl_quality")

    st.markdown("<div class='section-header'>Amendment Filings</div>", unsafe_allow_html=True)
    st.caption(
        "10-Q/A and 10-K/A filings indicate the company restated or corrected a previous filing. "
        "These are flagged only, not re-parsed through the main pipeline."
    )
    if amendments.empty:
        st.write("No amendment filings found for this company.")
    else:
        amendments_display = amendments.rename(columns={
            "form_type": "Form Type", "filing_date": "Filed", "period_end": "Amends Period",
        })
        st.dataframe(amendments_display[["Form Type", "Filed", "Amends Period"]], width='stretch')

    st.markdown("<div class='section-header'>Field Coverage (Current Quarter)</div>", unsafe_allow_html=True)
    st.caption(
        "How many holdings this quarter are missing a value for each field, and why that might be expected."
    )
    coverage = pd.DataFrame({
        "Field": ["Industry", "Reference Rate", "Risk Rating", "Non-Accrual Flag"],
        "Missing Count": [
            current_holdings["industry"].isna().sum(),
            current_holdings["reference_rate"].isna().sum(),
            current_holdings["risk_rating"].isna().sum(),
            0,
        ],
        "Total Rows": [len(current_holdings)] * 4,
        "Note": ["", "Blank means fixed rate or non-loan investment",
                 "Not yet parsed - risk rating disclosure location not yet confirmed for this filing",
                 "Derived from the filing's own footnote legend (detected fresh for each filing)"],
    })
    st.dataframe(coverage, width='stretch')
