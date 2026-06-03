"""Risk classification helpers."""
from __future__ import annotations


def classify_risk(investor_score: int, trader_score: int, allocation: float | None, news_risk: str = "low") -> str:
    if (allocation or 0) > 35 or news_risk == "high" or min(investor_score, trader_score) < 35:
        return "High"
    if (allocation or 0) > 25 or min(investor_score, trader_score) < 55:
        return "Medium"
    return "Low"
