from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.analysis.portfolio_context import enrich_portfolio_values
from src.analysis_engine import analyze_ticker
from src.charts import build_chart
from src.data_provider import DataProvider
from src.learning_engine import (
    STARTING_CAPITAL,
    has_pending_proposals,
    load_agent_portfolio,
    load_learning_log,
    portfolio_summary,
    record_decision,
    update_proposal_status,
)
from src.portfolio_health import analyze_portfolio_health

WATCHLIST_PATH = Path("data/watchlist.csv")
SUGGESTED_PATH = Path("data/suggested_stocks.csv")
DATA_UNAVAILABLE = "Data unavailable"
MANUAL_COLUMNS = ["use_by_agent", "ticker", "mode", "shares", "avg_price", "manual_position_size", "notes"]
AUTO_COLUMNS = ["current_price", "prev_close", "daily_change_$", "daily_change_%", "open", "day_high", "day_low", "volume", "avg_volume_20d", "relative_volume", "market_value", "cost_basis", "p_l_$", "p_l_%", "allocation_%", "sector", "industry", "market_cap", "beta", "52w_high", "52w_low", "distance_from_52w_high_%", "sma_20", "sma_50", "sma_150", "sma_200", "price_vs_sma_50", "price_vs_sma_200", "rsi_14", "atr_14", "daily_trend", "weekly_trend", "intraday_trend", "support", "resistance", "risk_level", "investor_score", "trader_score", "agent_decision", "action", "earnings_date", "latest_news_headline", "latest_filing", "last_scan", "data_status", "sources"]

st.set_page_config(page_title="Stock Agent MVP", layout="wide")


def ensure_files() -> None:
    Path("data").mkdir(exist_ok=True)
    if not WATCHLIST_PATH.exists():
        pd.DataFrame([{ "use_by_agent": True, "ticker": "AAPL", "mode": "Both", "shares": 0, "avg_price": 0, "manual_position_size": "", "notes": "Starter row" }]).to_csv(WATCHLIST_PATH, index=False)
    if not SUGGESTED_PATH.exists():
        pd.DataFrame(columns=["ticker", "reason", "catalyst", "source", "risk", "mode", "status"]).to_csv(SUGGESTED_PATH, index=False)


def load_watchlist() -> pd.DataFrame:
    ensure_files()
    df = pd.read_csv(WATCHLIST_PATH)
    for col in MANUAL_COLUMNS:
        if col not in df.columns:
            df[col] = False if col == "use_by_agent" else ""
    df["use_by_agent"] = df["use_by_agent"].astype(str).str.lower().isin(["true", "1", "yes"])
    return df[MANUAL_COLUMNS]


def save_watchlist(df: pd.DataFrame) -> None:
    df[MANUAL_COLUMNS].to_csv(WATCHLIST_PATH, index=False)


def fmt(value: Any) -> Any:
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        return DATA_UNAVAILABLE
    return value


def enrich_watchlist(manual_df: pd.DataFrame, provider: DataProvider, timeframe: str) -> tuple[pd.DataFrame, dict[str, dict]]:
    rows = []
    snapshots: dict[str, dict] = {}
    base = manual_df.copy()
    for _, row in base.iterrows():
        ticker = str(row.get("ticker", "")).upper().strip()
        if not ticker:
            continue
        snapshot = provider.full_snapshot(ticker, timeframe)
        snapshots[ticker] = snapshot
        merged = row.to_dict()
        merged.update(snapshot.get("quote", {}))
        merged.update({k: snapshot.get("profile", {}).get(k) for k in ["sector", "industry", "market_cap"]})
        merged.update({k: snapshot.get("indicators", {}).get(k) for k in ["avg_volume_20d", "relative_volume", "distance_from_52w_high_%", "sma_20", "sma_50", "sma_150", "sma_200", "price_vs_sma_50", "price_vs_sma_200", "rsi_14", "atr_14", "daily_trend", "weekly_trend", "intraday_trend"]})
        merged["earnings_date"] = snapshot.get("earnings", {}).get("next_earnings_date")
        filings = snapshot.get("filings", {}).get("filings", [])
        merged["latest_filing"] = filings[0].get("form_type") if filings else DATA_UNAVAILABLE
        news = snapshot.get("news", [])
        merged["latest_news_headline"] = news[0].get("headline") if news else DATA_UNAVAILABLE
        merged["last_scan"] = snapshot.get("sources", [{}])[0].get("timestamp", DATA_UNAVAILABLE) if snapshot.get("sources") else DATA_UNAVAILABLE
        merged["data_status"] = snapshot.get("data_status", DATA_UNAVAILABLE)
        merged["sources"] = json.dumps(snapshot.get("sources", []))
        rows.append(merged)
    enriched = enrich_portfolio_values(pd.DataFrame(rows)) if rows else pd.DataFrame(columns=MANUAL_COLUMNS + AUTO_COLUMNS)
    for _, row in enriched.iterrows():
        ticker = str(row.get("ticker", "")).upper()
        decision = analyze_ticker(ticker, row.get("mode", "Both"), snapshots[ticker], row.to_dict())
        enriched.loc[enriched["ticker"].astype(str).str.upper() == ticker, ["support", "resistance", "risk_level", "investor_score", "trader_score", "agent_decision", "action", "data_status", "sources"]] = [decision.get("support"), decision.get("resistance"), decision.get("risk_level"), decision.get("investor_score"), decision.get("trader_score"), decision.get("decision"), decision.get("action"), decision.get("data_status"), json.dumps(decision.get("sources", []))]
        if bool(row.get("use_by_agent")):
            record_decision(decision)
    for col in MANUAL_COLUMNS + AUTO_COLUMNS:
        if col not in enriched.columns:
            enriched[col] = DATA_UNAVAILABLE
    return enriched[MANUAL_COLUMNS + AUTO_COLUMNS], snapshots


def learning_log_page() -> None:
    st.title("Learning Log")
    st.caption("Rule proposals require user approval. No code or rule change is applied automatically.")
    rows = load_learning_log()
    if not rows:
        st.info("No learning proposals yet.")
        return
    for row in rows:
        with st.container(border=True):
            st.subheader(f"{row.get('id')} — {row.get('status')}")
            st.write("**What was wrong:**", row.get("problem", DATA_UNAVAILABLE))
            st.write("**Evidence:**", row.get("evidence", DATA_UNAVAILABLE))
            st.write("**Old rule:**", row.get("old_rule", DATA_UNAVAILABLE))
            st.write("**New rule:**", row.get("new_rule", DATA_UNAVAILABLE))
            st.write("**Proposed code change:**", row.get("proposed_code_change", DATA_UNAVAILABLE))
            st.write("**Expected improvement:**", row.get("expected_improvement", DATA_UNAVAILABLE))
            st.write("**Risk of change:**", row.get("risk_of_change", DATA_UNAVAILABLE))
            c1, c2 = st.columns(2)
            if c1.button("Approve", key=f"approve_{row.get('id')}"):
                update_proposal_status(row.get("id"), "Approved")
                st.rerun()
            if c2.button("Reject", key=f"reject_{row.get('id')}"):
                update_proposal_status(row.get("id"), "Rejected")
                st.rerun()


def main() -> None:
    if st.query_params.get("page") == "learning_log":
        learning_log_page()
        return
    st.title("Stock Agent Dashboard")
    provider = DataProvider()
    top_controls = st.columns([1, 1, 1, 1])
    timeframe = top_controls[0].selectbox("Timeframe", ["5m", "15m", "1h", "1d", "1wk"], index=3)
    chart_type = top_controls[1].selectbox("Chart type", ["candles", "line"])
    sma_windows = top_controls[2].multiselect("SMA", [20, 50, 150, 200], default=[20, 50])
    right_width = top_controls[3].slider("Right panel width", 20, 50, 30)

    manual = load_watchlist()
    with st.spinner("Scanning live providers with mock fallback..."):
        enriched, snapshots = enrich_watchlist(manual, provider, timeframe)
    health = analyze_portfolio_health(enriched, cash=None)
    investor_summary = enriched.sort_values("investor_score", ascending=False).iloc[0]["ticker"] if not enriched.empty else DATA_UNAVAILABLE
    trading_summary = enriched.sort_values("trader_score", ascending=False).iloc[0]["ticker"] if not enriched.empty else DATA_UNAVAILABLE

    hcols = st.columns(8)
    hcols[0].metric("Portfolio Health", health["status"])
    hcols[1].metric("Investor summary", investor_summary)
    hcols[2].metric("Trading summary", trading_summary)
    hcols[3].write(f"**Main risk**  \n{health['main_risk']}")
    hcols[4].write(f"**Best setup**  \n{health['best_position']}")
    hcols[5].write(f"**Weakest setup**  \n{health['weakest_position']}")
    hcols[6].write(f"**Cash status**  \n{health['cash_comment']}")
    button_type = "primary" if has_pending_proposals() else "secondary"
    if hcols[7].button("Learning Log", type=button_type):
        st.query_params["page"] = "learning_log"
        st.rerun()

    left_w = max(20, 70 - right_width)
    center_w = 50
    left, center, right = st.columns([left_w, center_w, right_width])

    with right:
        st.subheader("Watchlist / Portfolio")
        edited = st.data_editor(manual, use_container_width=True, num_rows="dynamic", column_config={"use_by_agent": st.column_config.CheckboxColumn("use_by_agent"), "mode": st.column_config.SelectboxColumn("mode", options=["Investor", "Trading", "Both"])})
        if st.button("Save watchlist"):
            save_watchlist(edited)
            st.success("Saved")
            st.rerun()
        st.dataframe(enriched, use_container_width=True, height=420)
        st.subheader("Suggested Stocks by Agent")
        st.dataframe(pd.read_csv(SUGGESTED_PATH), use_container_width=True)

    selected = center.selectbox("Select ticker", enriched["ticker"].tolist() if not enriched.empty else [DATA_UNAVAILABLE])
    row = enriched[enriched["ticker"] == selected].iloc[0].to_dict() if selected != DATA_UNAVAILABLE else {}
    snapshot = snapshots.get(selected, {})
    decision = analyze_ticker(selected, row.get("mode", "Both"), snapshot, row) if row else {}

    with left:
        st.subheader("Compact Agent Summary")
        st.write(f"**Decision:** {decision.get('decision', DATA_UNAVAILABLE)}")
        st.write(f"**Action:** {decision.get('action', DATA_UNAVAILABLE)}")
        st.write(f"**Risk:** {decision.get('risk_level', DATA_UNAVAILABLE)}")
        st.write(f"**Reason:** {decision.get('key_reason', DATA_UNAVAILABLE)}")
        with st.expander("Show full analysis", expanded=False):
            st.json(decision)
        st.subheader("Agent Portfolio Learning Tool")
        agent_df = load_agent_portfolio()
        summary = portfolio_summary(agent_df)
        st.write(f"Starting capital: ${STARTING_CAPITAL:,.0f}")
        st.write(f"Cash: ${summary['cash']:,.2f} | Realized P/L: ${summary['realized_p_l']:,.2f} | Unrealized P/L: ${summary['unrealized_p_l']:,.2f}")
        st.dataframe(agent_df, use_container_width=True)
        if st.button("Learning Log", type=button_type, key="learning_left"):
            st.query_params["page"] = "learning_log"
            st.rerun()

    with center:
        st.subheader("Interactive Charts")
        st.caption("Use Plotly modebar drawing tools for horizontal lines/trendlines and erasing drawings. Max 3 charts visible.")
        tickers = enriched["ticker"].head(3).tolist() if not enriched.empty else []
        primary = [selected] + [t for t in tickers if t != selected]
        for ticker in primary[:3]:
            frame = snapshots.get(ticker, {}).get("ohlcv", pd.DataFrame())
            st.plotly_chart(build_chart(frame, ticker, chart_type, sma_windows), use_container_width=True)

    st.caption("No real trading execution. External data is live when providers succeed; otherwise rows are marked Data unavailable/mock fallback with sources and timestamps.")


if __name__ == "__main__":
    main()
