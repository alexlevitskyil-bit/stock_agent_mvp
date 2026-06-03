"""Portfolio context calculations."""
from __future__ import annotations

import pandas as pd


def enrich_portfolio_values(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["shares", "avg_price", "current_price"]:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["market_value"] = out["shares"] * out["current_price"]
    out["cost_basis"] = out["shares"] * out["avg_price"]
    out["p_l_$"] = out["market_value"] - out["cost_basis"]
    out["p_l_%"] = out.apply(lambda r: (r["p_l_$"] / r["cost_basis"] * 100) if r["cost_basis"] else 0, axis=1)
    total = out["market_value"].sum()
    out["allocation_%"] = out["market_value"].apply(lambda v: v / total * 100 if total else 0)
    return out
