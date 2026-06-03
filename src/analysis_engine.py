"""Compatibility wrapper for dashboard analysis."""
from __future__ import annotations

from src.analysis.decision_engine import build_decision


def analyze_ticker(ticker: str, mode: str, snapshot: dict, portfolio_row: dict) -> dict:
    return build_decision(
        ticker=ticker,
        mode=mode,
        quote=snapshot.get("quote", {}),
        indicators=snapshot.get("indicators", {}),
        fundamentals=snapshot.get("fundamentals", {}),
        portfolio_row=portfolio_row,
        ohlcv=snapshot.get("ohlcv"),
        news_rows=snapshot.get("news", []),
        sources=snapshot.get("sources", []),
        data_status=snapshot.get("data_status", "Data unavailable"),
    )
