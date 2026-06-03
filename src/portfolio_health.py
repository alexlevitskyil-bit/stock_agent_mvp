"""Portfolio health assessment."""
from __future__ import annotations

import pandas as pd


def analyze_portfolio_health(df: pd.DataFrame, cash: float | None = None) -> dict:
    if df.empty:
        return {"status": "Neutral", "short_comment": "No positions to analyze", "main_risk": "Data unavailable", "best_position": "Data unavailable", "weakest_position": "Data unavailable", "cash_comment": "Cash unavailable", "concentration_warning": "Data unavailable", "sector_concentration": "Data unavailable", "high_risk_names": [], "earnings_risk_names": [], "suggested_action": "Add watchlist rows"}
    total = pd.to_numeric(df.get("market_value", 0), errors="coerce").fillna(0).sum()
    largest = df.loc[pd.to_numeric(df.get("allocation_%", 0), errors="coerce").fillna(0).idxmax()] if total else df.iloc[0]
    largest_alloc = float(largest.get("allocation_%", 0) or 0)
    high_risk = df[df.get("risk_level", "").astype(str).str.lower() == "high"]["ticker"].astype(str).tolist() if "risk_level" in df else []
    sector_conc = "Data unavailable"
    if "sector" in df and total:
        sector_values = df.groupby("sector")["market_value"].sum().sort_values(ascending=False)
        if not sector_values.empty:
            sector_conc = f"{sector_values.index[0]}: {sector_values.iloc[0] / total * 100:.1f}%"
    status = "Healthy"
    warnings = []
    if largest_alloc > 35:
        status = "Risky"; warnings.append(f"largest position {largest.get('ticker')} exceeds 35%")
    elif largest_alloc > 25:
        status = "Neutral"; warnings.append(f"largest position {largest.get('ticker')} exceeds 25%")
    if len(high_risk) >= 3:
        status = "Risky"; warnings.append("too many high-risk stocks")
    best = df.sort_values("investor_score", ascending=False).iloc[0].get("ticker") if "investor_score" in df else "Data unavailable"
    weakest = df.sort_values("investor_score", ascending=True).iloc[0].get("ticker") if "investor_score" in df else "Data unavailable"
    earnings_risk = df[df.get("earnings_date", "").astype(str).ne("")]["ticker"].astype(str).tolist() if "earnings_date" in df else []
    return {"status": status, "short_comment": "Portfolio checks complete", "main_risk": "; ".join(warnings) or "No major rule-based risk detected", "best_position": best, "weakest_position": weakest, "cash_comment": f"Cash: ${cash:,.2f}" if cash is not None else "Cash unavailable", "concentration_warning": "; ".join(warnings) or "No concentration warning", "sector_concentration": sector_conc, "high_risk_names": high_risk, "earnings_risk_names": earnings_risk, "suggested_action": "Review high-risk and concentrated positions" if warnings or high_risk else "Maintain review cadence"}
