"""Provider interfaces used by the stock dashboard."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd

DATA_UNAVAILABLE = "Data unavailable"


@dataclass
class ProviderResult:
    data: dict[str, Any] = field(default_factory=dict)
    status: str = DATA_UNAVAILABLE
    sources: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""


class BaseProvider:
    name = "base"

    def quote(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="quote not implemented")

    def ohlcv(self, ticker: str, timeframe: str) -> tuple[pd.DataFrame, ProviderResult]:
        return pd.DataFrame(), ProviderResult(error="ohlcv not implemented")

    def profile(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="profile not implemented")

    def fundamentals(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="fundamentals not implemented")

    def filings(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="filings not implemented")

    def news(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="news not implemented")

    def earnings(self, ticker: str) -> ProviderResult:
        return ProviderResult(error="earnings not implemented")
