"""Technical indicator calculations."""
from __future__ import annotations

import numpy as np
import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    close = out["close"].astype(float)
    for window in [20, 50, 150, 200]:
        out[f"sma_{window}"] = close.rolling(window, min_periods=1).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi_14"] = (100 - (100 / (1 + rs))).fillna(50)
    tr = pd.concat([(out["high"] - out["low"]).abs(), (out["high"] - close.shift()).abs(), (out["low"] - close.shift()).abs()], axis=1).max(axis=1)
    out["atr_14"] = tr.rolling(14, min_periods=1).mean()
    pv = (out["close"] * out["volume"].fillna(0)).cumsum()
    vol = out["volume"].fillna(0).cumsum().replace(0, np.nan)
    out["vwap"] = (pv / vol).fillna(out["close"])
    out["avg_volume_20d"] = out["volume"].rolling(20, min_periods=1).mean()
    out["relative_volume"] = out["volume"] / out["avg_volume_20d"].replace(0, np.nan)
    return out


def latest_indicator_snapshot(df: pd.DataFrame, quote: dict) -> dict:
    if df.empty:
        return {}
    frame = add_indicators(df)
    row = frame.iloc[-1].to_dict()
    price = quote.get("current_price") or row.get("close")
    hi52 = quote.get("52w_high")
    row["price_vs_sma_50"] = _distance(price, row.get("sma_50"))
    row["price_vs_sma_200"] = _distance(price, row.get("sma_200"))
    row["distance_from_52w_high_%"] = _distance(price, hi52)
    row["daily_trend"] = "Healthy" if price and row.get("sma_50") and price >= row.get("sma_50") else "Weak"
    row["weekly_trend"] = "Healthy" if price and row.get("sma_200") and price >= row.get("sma_200") else "Weak"
    row["intraday_trend"] = "Above VWAP" if price and row.get("vwap") and price >= row.get("vwap") else "Below VWAP"
    return row


def _distance(price, base):
    if price is None or base in (None, 0):
        return None
    return (price - base) / base * 100
