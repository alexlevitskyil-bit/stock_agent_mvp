"""High-level provider orchestrator with live-first priority and mock fallback."""
from __future__ import annotations

from dotenv import load_dotenv
import pandas as pd

from src.analysis.indicators import latest_indicator_snapshot
from src.providers.base import DATA_UNAVAILABLE, ProviderResult
from src.providers.finnhub_provider import FinnhubProvider
from src.providers.mock_provider import MockProvider
from src.providers.sec_provider import SECProvider
from src.providers.source_registry import save_sources
from src.providers.yfinance_provider import YFinanceProvider

load_dotenv()


class DataProvider:
    def __init__(self) -> None:
        self.yf = YFinanceProvider()
        self.sec = SECProvider()
        self.finnhub = FinnhubProvider()
        self.mock = MockProvider()

    def quote(self, ticker: str) -> ProviderResult:
        result = self.yf.quote(ticker)
        if result.data:
            save_sources(ticker, result.sources)
            return result
        fallback = self.mock.quote(ticker)
        fallback.error = result.error
        save_sources(ticker, fallback.sources)
        return fallback

    def ohlcv(self, ticker: str, timeframe: str) -> tuple[pd.DataFrame, ProviderResult]:
        frame, result = self.yf.ohlcv(ticker, timeframe)
        if not frame.empty:
            return frame, result
        fallback_frame, fallback = self.mock.ohlcv(ticker, timeframe)
        fallback.error = result.error
        return fallback_frame, fallback

    def profile(self, ticker: str) -> ProviderResult:
        result = self.yf.profile(ticker)
        return result if result.data else self.mock.profile(ticker)

    def fundamentals(self, ticker: str) -> ProviderResult:
        return self.yf.fundamentals(ticker)

    def filings(self, ticker: str) -> ProviderResult:
        return self.sec.filings(ticker)

    def news(self, ticker: str) -> ProviderResult:
        finnhub = self.finnhub.news(ticker)
        if finnhub.data.get("headlines"):
            return finnhub
        return self.yf.news(ticker)

    def earnings(self, ticker: str) -> ProviderResult:
        finnhub = self.finnhub.earnings(ticker)
        return finnhub if finnhub.data else self.yf.earnings(ticker)

    def full_snapshot(self, ticker: str, timeframe: str = "1d") -> dict:
        quote = self.quote(ticker)
        ohlcv, ohlcv_result = self.ohlcv(ticker, timeframe)
        profile = self.profile(ticker)
        fundamentals = self.fundamentals(ticker)
        filings = self.filings(ticker)
        news = self.news(ticker)
        earnings = self.earnings(ticker)
        indicators = latest_indicator_snapshot(ohlcv, quote.data)
        sources = quote.sources + ohlcv_result.sources + profile.sources + fundamentals.sources + filings.sources + news.sources + earnings.sources
        status_parts = [r.status for r in [quote, ohlcv_result, profile, fundamentals, filings, news, earnings] if r.status]
        return {"quote": quote.data, "ohlcv": ohlcv, "profile": profile.data, "fundamentals": fundamentals.data, "filings": filings.data, "news": news.data.get("headlines", []), "earnings": earnings.data, "indicators": indicators, "sources": sources, "data_status": " | ".join(status_parts) or DATA_UNAVAILABLE}
