"""Mock fallback provider. Values are labeled unavailable, not fabricated live facts."""
from __future__ import annotations

import pandas as pd

from .base import BaseProvider, DATA_UNAVAILABLE, ProviderResult
from .source_registry import make_source


class MockProvider(BaseProvider):
    name = "Mock fallback"

    def quote(self, ticker: str) -> ProviderResult:
        source = make_source(self.name, "local mock_provider.py", "Fallback used because live provider failed")
        return ProviderResult(
            data={
                "ticker": ticker.upper(),
                "current_price": None,
                "prev_close": None,
                "open": None,
                "day_high": None,
                "day_low": None,
                "daily_change_$": None,
                "daily_change_%": None,
                "volume": None,
                "avg_volume_20d": None,
                "market_cap": None,
                "beta": None,
                "52w_high": None,
                "52w_low": None,
                "exchange": DATA_UNAVAILABLE,
                "currency": DATA_UNAVAILABLE,
            },
            status="Mock fallback only - live data unavailable",
            sources=[source],
        )

    def ohlcv(self, ticker: str, timeframe: str) -> tuple[pd.DataFrame, ProviderResult]:
        # Never return synthetic prices for OHLCV fallback: an empty frame prevents
        # downstream indicators, support/resistance, scores, and charts from being
        # computed from invented market data.
        columns = ["datetime", "open", "high", "low", "close", "volume"]
        frame = pd.DataFrame(columns=columns)
        return frame, ProviderResult(status="Mock fallback only - live OHLCV unavailable", sources=[make_source(self.name, "local mock_provider.py")])

    def profile(self, ticker: str) -> ProviderResult:
        return ProviderResult(data={"sector": DATA_UNAVAILABLE, "industry": DATA_UNAVAILABLE}, status="Mock fallback only", sources=[make_source(self.name, "local mock_provider.py")])
