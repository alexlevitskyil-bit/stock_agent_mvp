"""Investor-mode scoring and action logic."""
from __future__ import annotations


def analyze_investor(ticker: str, quote: dict, indicators: dict, fundamentals: dict, portfolio_row: dict, news_risk: str) -> dict:
    score = 50
    reasons = []
    if indicators.get("weekly_trend") == "Healthy": score += 12
    else: reasons.append("weekly trend weak")
    if indicators.get("daily_trend") == "Healthy": score += 10
    else: reasons.append("daily trend weak")
    if (indicators.get("price_vs_sma_50") or -999) > 0: score += 8
    if (indicators.get("price_vs_sma_200") or -999) > 0: score += 8
    if fundamentals.get("profit_margin") is not None and fundamentals.get("profit_margin") > 0: score += 8
    if news_risk == "high": score -= 10; reasons.append("news risk high")
    allocation = portfolio_row.get("allocation_%") or 0
    if allocation > 35: score -= 18; reasons.append("allocation too high")
    elif allocation > 25: score -= 8; reasons.append("allocation elevated")
    extended = (indicators.get("price_vs_sma_50") or 0) > 12
    if extended: score -= 8; reasons.append("price extended")
    score = max(0, min(100, round(score)))
    decision = "Add" if score >= 75 and not extended else "Hold" if score >= 60 else "Wait" if score >= 40 else "Avoid"
    if allocation > 35:
        decision = "Trim"
    return {"mode": "Investor", "decision": decision, "score": score, "key_reason": "; ".join(reasons) or "trend and portfolio checks acceptable", "weekly_trend_healthy": indicators.get("weekly_trend"), "daily_trend_healthy": indicators.get("daily_trend"), "price_extended": extended, "rr_attractive": None, "allocation_too_high": allocation > 25, "portfolio_fit": "Check allocation and sector concentration"}
