"""Combined Investor and Trading Mode decision engine."""
from __future__ import annotations

from .investor_engine import analyze_investor
from .levels import recent_support_resistance
from .news_engine import summarize_news
from .risk_engine import classify_risk
from .trading_engine import analyze_trading


def build_decision(ticker: str, mode: str, quote: dict, indicators: dict, fundamentals: dict, portfolio_row: dict, ohlcv, news_rows: list[dict], sources: list[dict], data_status: str) -> dict:
    support, resistance = recent_support_resistance(ohlcv)
    news = summarize_news(news_rows)
    investor = analyze_investor(ticker, quote, indicators, fundamentals, portfolio_row, news.get("news_risk", "low"))
    trading = analyze_trading(ticker, quote, indicators, support, resistance)
    risk = classify_risk(investor["score"], trading["score"], portfolio_row.get("allocation_%"), news.get("news_risk", "low"))
    if mode == "Investor":
        decision, action, reason = investor["decision"], investor["decision"], investor["key_reason"]
    elif mode == "Trading":
        decision, action, reason = trading["decision"], trading["decision"], trading["key_reason"]
    else:
        decision = f"Investor: {investor['decision']} / Trading: {trading['decision']}"
        action = "Review both modes"
        reason = f"Investor: {investor['key_reason']} | Trading: {trading['key_reason']}"
    return {"ticker": ticker.upper(), "mode": mode, "decision": decision, "action": action, "investor_score": investor["score"], "trader_score": trading["score"], "risk_level": risk, "key_reason": reason, "support": support, "resistance": resistance, "stop": trading.get("stop"), "target_1": trading.get("target_1"), "target_2": trading.get("target_2"), "rr_ratio": trading.get("rr_ratio"), "data_status": data_status, "sources": sources, "investor": investor, "trading": trading, **news}
