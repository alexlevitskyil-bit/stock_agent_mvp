"""Simple transparent news risk and catalyst helpers."""
from __future__ import annotations

NEGATIVE = ["lawsuit", "probe", "miss", "downgrade", "cut", "fraud", "bankruptcy", "sec"]
POSITIVE = ["beat", "upgrade", "raise", "approval", "contract", "launch"]


def summarize_news(news_rows: list[dict]) -> dict:
    if not news_rows:
        return {"latest_news_headline": "Data unavailable", "news_risk": "unknown", "sentiment": "neutral"}
    headline = news_rows[0].get("headline") or "Data unavailable"
    blob = " ".join(str(row.get("headline", "")).lower() for row in news_rows)
    if any(word in blob for word in NEGATIVE):
        return {"latest_news_headline": headline, "news_risk": "high", "sentiment": "negative"}
    if any(word in blob for word in POSITIVE):
        return {"latest_news_headline": headline, "news_risk": "low", "sentiment": "positive"}
    return {"latest_news_headline": headline, "news_risk": "low", "sentiment": "neutral"}
