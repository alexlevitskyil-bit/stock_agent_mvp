"""Plotly chart rendering with drawing tools."""
from __future__ import annotations

import plotly.graph_objects as go

from src.analysis.indicators import add_indicators


def build_chart(df, ticker: str, chart_type: str = "candles", sma_windows: list[int] | None = None):
    sma_windows = sma_windows or []
    frame = add_indicators(df)
    fig = go.Figure()
    if frame.empty:
        fig.update_layout(title=f"{ticker}: Data unavailable")
        return fig
    if chart_type == "candles":
        fig.add_trace(go.Candlestick(x=frame["datetime"], open=frame["open"], high=frame["high"], low=frame["low"], close=frame["close"], name=ticker))
    else:
        fig.add_trace(go.Scatter(x=frame["datetime"], y=frame["close"], mode="lines", name=ticker))
    for window in sma_windows[:4]:
        col = f"sma_{window}"
        if col in frame:
            fig.add_trace(go.Scatter(x=frame["datetime"], y=frame[col], mode="lines", name=f"SMA {window}"))
    fig.update_layout(
        title=f"{ticker} chart",
        height=330,
        margin={"l": 20, "r": 20, "t": 35, "b": 20},
        xaxis_rangeslider_visible=False,
        dragmode="drawline",
        newshape={"line_color": "cyan"},
        modebar_add=["drawline", "drawopenpath", "drawrect", "eraseshape"],
    )
    return fig
