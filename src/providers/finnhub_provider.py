"""Optional Finnhub provider for news, earnings, and analyst data."""
from __future__ import annotations

from datetime import date, timedelta
import os
import requests

from .base import BaseProvider, DATA_UNAVAILABLE, ProviderResult
from .source_registry import make_source


class FinnhubProvider(BaseProvider):
    name = "Finnhub"

    def __init__(self) -> None:
        self.api_key = os.getenv("FINNHUB_API_KEY", "").strip()
        self.enabled = bool(self.api_key)

    def _get(self, path: str, params: dict) -> list | dict:
        params = {**params, "token": self.api_key}
        return requests.get(f"https://finnhub.io/api/v1/{path}", params=params, timeout=15).json()

    def news(self, ticker: str) -> ProviderResult:
        if not self.enabled:
            return ProviderResult(status=DATA_UNAVAILABLE, error="FINNHUB_API_KEY missing; Finnhub provider disabled")
        try:
            today = date.today()
            rows = self._get("company-news", {"symbol": ticker.upper(), "from": str(today - timedelta(days=14)), "to": str(today)})
            headlines = [{"headline": r.get("headline"), "publisher": r.get("source"), "date": r.get("datetime"), "url": r.get("url"), "ticker": ticker.upper(), "sentiment": "neutral", "catalyst_type": _catalyst(r.get("headline", ""))} for r in rows[:5]] if isinstance(rows, list) else []
            return ProviderResult(data={"headlines": headlines}, status="Live" if headlines else DATA_UNAVAILABLE, sources=[make_source(self.name, "https://finnhub.io/docs/api/company-news")])
        except Exception as exc:
            return ProviderResult(error=str(exc))

    def earnings(self, ticker: str) -> ProviderResult:
        if not self.enabled:
            return ProviderResult(status=DATA_UNAVAILABLE, error="FINNHUB_API_KEY missing; Finnhub provider disabled")
        try:
            rows = self._get("calendar/earnings", {"symbol": ticker.upper()})
            return ProviderResult(data={"earnings_calendar": rows}, status="Live", sources=[make_source(self.name, "https://finnhub.io/docs/api/earnings-calendar")])
        except Exception as exc:
            return ProviderResult(error=str(exc))


def _catalyst(headline: str) -> str:
    h = headline.lower()
    for word in ["earnings", "guidance", "analyst", "product", "legal", "macro", "insider"]:
        if word in h:
            return word
    return "sector"
