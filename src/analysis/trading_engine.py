"""Trading-mode scoring and action logic."""
from __future__ import annotations

from .levels import trade_levels


def analyze_trading(ticker: str, quote: dict, indicators: dict, support, resistance) -> dict:
    price = quote.get("current_price") or indicators.get("close")
    stop, target_1, target_2, rr = trade_levels(price, support, resistance, indicators.get("atr_14"))
    score = 45
    reasons = []
    if indicators.get("intraday_trend") == "Above VWAP": score += 15
    else: reasons.append("below VWAP")
    if (indicators.get("relative_volume") or 0) >= 1.2: score += 12
    else: reasons.append("volume not confirmed")
    if price and resistance and price > resistance * 0.98: score += 10
    if rr is not None and rr >= 1.5: score += 15
    else: reasons.append("risk/reward unattractive or unavailable")
    if (indicators.get("rsi_14") or 50) > 75: score -= 12; reasons.append("extended RSI")
    score = max(0, min(100, round(score)))
    decision = "Trade setup" if score >= 70 else "Wait" if score >= 40 else "Avoid"
    return {"mode": "Trading", "decision": decision, "score": score, "key_reason": "; ".join(reasons) or "VWAP, volume, and R/R checks acceptable", "vwap_position": indicators.get("intraday_trend"), "opening_range_high": None, "opening_range_low": None, "day_high": quote.get("day_high"), "day_low": quote.get("day_low"), "stop": stop, "target_1": target_1, "target_2": target_2, "rr_ratio": rr}
