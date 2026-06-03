"""Support/resistance and trade level helpers."""
from __future__ import annotations

import pandas as pd


def recent_support_resistance(df: pd.DataFrame) -> tuple[float | None, float | None]:
    if df.empty:
        return None, None
    recent = df.tail(30)
    return float(recent["low"].min()), float(recent["high"].max())


def trade_levels(price, support, resistance, atr):
    if price is None:
        return None, None, None, None
    stop = support if support is not None else (price - atr if atr else None)
    target_1 = resistance if resistance is not None else (price + atr if atr else None)
    target_2 = (price + 2 * (target_1 - price)) if target_1 is not None else None
    risk = price - stop if stop is not None else None
    reward = target_1 - price if target_1 is not None else None
    rr = reward / risk if risk and risk > 0 and reward is not None else None
    return stop, target_1, target_2, rr
