"""Mock fallback provider. Values are labeled unavailable, not fabricated live facts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import numpy as np
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
        now = datetime.now(timezone.utc)
        dates = [now - timedelta(days=i) for i in range(90)][::-1]
        # Minimal non-financial placeholder series so charts remain usable and visibly labeled fallback.
        base = np.linspace(100, 100, len(dates))
        frame = pd.DataFrame({"datetime": dates, "open": base, "high": base, "low": base, "close": base, "volume": 0})
        return frame, ProviderResult(status="Mock fallback only - live OHLCV unavailable", sources=[make_source(self.name, "local mock_provider.py")])

    def profile(self, ticker: str) -> ProviderResult:
        return ProviderResult(data={"sector": DATA_UNAVAILABLE, "industry": DATA_UNAVAILABLE}, status="Mock fallback only", sources=[make_source(self.name, "local mock_provider.py")])
