"""yfinance market, OHLCV, profile, fundamental, news, and earnings provider."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import pandas as pd
import yfinance as yf

from .base import BaseProvider, DATA_UNAVAILABLE, ProviderResult
from .source_registry import make_source

PERIOD_BY_TIMEFRAME = {"5m": "5d", "15m": "1mo", "1h": "3mo", "1d": "1y", "1wk": "5y"}


def _get(info: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        val = info.get(key)
        if val is not None and val != "":
            return val
    return None


class YFinanceProvider(BaseProvider):
    name = "Yahoo Finance via yfinance"

    def _ticker(self, ticker: str):
        return yf.Ticker(ticker.upper())

    def quote(self, ticker: str) -> ProviderResult:
        try:
            t = self._ticker(ticker)
            info = t.get_info()
            hist = t.history(period="1mo", interval="1d", auto_adjust=False)
            current = _get(info, "regularMarketPrice", "currentPrice")
            prev = _get(info, "regularMarketPreviousClose", "previousClose")
            if current is None and not hist.empty:
                current = float(hist["Close"].dropna().iloc[-1])
            if prev is None and len(hist.dropna()) > 1:
                prev = float(hist["Close"].dropna().iloc[-2])
            change = (current - prev) if current is not None and prev is not None else None
            change_pct = (change / prev * 100) if change is not None and prev else None
            avg_volume = float(hist["Volume"].tail(20).mean()) if not hist.empty else _get(info, "averageVolume")
            source = make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}", "quote/profile/fundamental data")
            return ProviderResult(data={
                "ticker": ticker.upper(), "current_price": current, "prev_close": prev,
                "open": _get(info, "regularMarketOpen", "open"), "day_high": _get(info, "regularMarketDayHigh", "dayHigh"),
                "day_low": _get(info, "regularMarketDayLow", "dayLow"), "daily_change_$": change, "daily_change_%": change_pct,
                "volume": _get(info, "regularMarketVolume", "volume"), "avg_volume_20d": avg_volume,
                "market_cap": _get(info, "marketCap"), "beta": _get(info, "beta"),
                "52w_high": _get(info, "fiftyTwoWeekHigh"), "52w_low": _get(info, "fiftyTwoWeekLow"),
                "exchange": _get(info, "exchange"), "currency": _get(info, "currency"),
            }, status="Live", sources=[source])
        except Exception as exc:
            return ProviderResult(error=str(exc))

    def ohlcv(self, ticker: str, timeframe: str) -> tuple[pd.DataFrame, ProviderResult]:
        try:
            period = PERIOD_BY_TIMEFRAME.get(timeframe, "1y")
            hist = self._ticker(ticker).history(period=period, interval=timeframe, auto_adjust=False)
            if hist.empty:
                return pd.DataFrame(), ProviderResult(error="empty history")
            hist = hist.reset_index()
            date_col = "Datetime" if "Datetime" in hist.columns else "Date"
            frame = hist.rename(columns={date_col: "datetime", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
            return frame[["datetime", "open", "high", "low", "close", "volume"]], ProviderResult(status="Live", sources=[make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}/chart", f"OHLCV {timeframe}")])
        except Exception as exc:
            return pd.DataFrame(), ProviderResult(error=str(exc))

    def profile(self, ticker: str) -> ProviderResult:
        try:
            info = self._ticker(ticker).get_info()
            data = {"company_name": _get(info, "longName", "shortName"), "sector": _get(info, "sector"), "industry": _get(info, "industry"), "country": _get(info, "country"), "website": _get(info, "website"), "business_summary": _get(info, "longBusinessSummary"), "employees": _get(info, "fullTimeEmployees"), "exchange": _get(info, "exchange"), "market_cap": _get(info, "marketCap")}
            return ProviderResult(data=data, status="Live", sources=[make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}/profile")])
        except Exception as exc:
            return ProviderResult(error=str(exc))

    def fundamentals(self, ticker: str) -> ProviderResult:
        try:
            info = self._ticker(ticker).get_info()
            keys = {"trailing_pe":"trailingPE", "forward_pe":"forwardPE", "price_sales":"priceToSalesTrailing12Months", "price_book":"priceToBook", "eps":"trailingEps", "revenue":"totalRevenue", "revenue_growth":"revenueGrowth", "gross_margin":"grossMargins", "operating_margin":"operatingMargins", "profit_margin":"profitMargins", "free_cash_flow":"freeCashflow", "total_cash":"totalCash", "total_debt":"totalDebt", "debt_equity":"debtToEquity", "return_on_equity":"returnOnEquity", "return_on_assets":"returnOnAssets", "analyst_target_price":"targetMeanPrice", "recommendation_mean":"recommendationMean", "number_of_analysts":"numberOfAnalystOpinions"}
            return ProviderResult(data={out: _get(info, src) for out, src in keys.items()}, status="Live", sources=[make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}/key-statistics")])
        except Exception as exc:
            return ProviderResult(error=str(exc))

    def news(self, ticker: str) -> ProviderResult:
        try:
            news = self._ticker(ticker).news or []
            rows = []
            for item in news[:5]:
                content = item.get("content", item)
                ts = content.get("pubDate") or content.get("displayTime") or datetime.now(timezone.utc).isoformat()
                rows.append({"headline": content.get("title"), "publisher": (content.get("provider") or {}).get("displayName"), "date": ts, "url": (content.get("canonicalUrl") or {}).get("url"), "ticker": ticker.upper(), "sentiment": "neutral", "catalyst_type": "sector"})
            return ProviderResult(data={"headlines": rows}, status="Live" if rows else DATA_UNAVAILABLE, sources=[make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}/news")])
        except Exception as exc:
            return ProviderResult(error=str(exc))

    def earnings(self, ticker: str) -> ProviderResult:
        try:
            cal = self._ticker(ticker).calendar
            data = {"next_earnings_date": None, "last_earnings_date": None, "eps_estimate": None, "eps_actual": None, "revenue_estimate": None, "revenue_actual": None, "surprise": None}
            if isinstance(cal, dict):
                data["next_earnings_date"] = cal.get("Earnings Date")
            return ProviderResult(data=data, status="Live", sources=[make_source(self.name, f"https://finance.yahoo.com/quote/{ticker.upper()}/analysis")])
        except Exception as exc:
            return ProviderResult(error=str(exc))
