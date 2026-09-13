"""Reusable Plotly chart + gauge helpers for the Streamlit AIoT dashboard.

No Streamlit UI code here — only pure Plotly Figure builders so they can be
unit-tested or reused outside Streamlit.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# Gauge (single-value indicator).
# ---------------------------------------------------------------------------
def gauge(
    value: float,
    min_v: float,
    max_v: float,
    label: str,
    unit: str,
    danger_threshold: Optional[float] = None,
    warning_threshold: Optional[float] = None,
    lower_is_bad: bool = False,
) -> go.Figure:
    """A small Plotly radial indicator gauge with optional danger/warning bands.

    If ``danger_threshold`` is given:
    * ``lower_is_bad=False`` (default): values above threshold are colored red.
    * ``lower_is_bad=True`` : values below threshold are colored red.
    Warning threshold, if provided, sits between green and red.
    """
    value = float(value) if not pd.isna(value) else float(min_v)
    value = float(np.clip(value, min_v, max_v))

    steps = []
    if danger_threshold is not None:
        if warning_threshold is None:
            warning_threshold = danger_threshold - 0.2 * (max_v - min_v)
        if not lower_is_bad:
            steps = [
                {"range": [min_v, warning_threshold], "color": "#2ecc71"},
                {"range": [warning_threshold, danger_threshold], "color": "#f1c40f"},
                {"range": [danger_threshold, max_v], "color": "#e74c3c"},
            ]
        else:
            steps = [
                {"range": [min_v, danger_threshold], "color": "#e74c3c"},
                {"range": [danger_threshold, warning_threshold], "color": "#f1c40f"},
                {"range": [warning_threshold, max_v], "color": "#2ecc71"},
            ]
    else:
        steps = [{"range": [min_v, max_v], "color": "#3498db"}]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"{label}<br><span style='font-size:0.7em;color:gray'>{unit}</span>"},
            gauge={
                "axis": {"range": [min_v, max_v]},
                "bar": {"color": "#2c3e50", "thickness": 0.35},
                "steps": steps,
                "threshold": {
                    "line": {"color": "#2c3e50", "width": 2},
                    "thickness": 0.75,
                    "value": value,
                },
            },
            number={"font": {"size": 36}, "valueformat": ".1f"},
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# ---------------------------------------------------------------------------
# Time-series chart.
# ---------------------------------------------------------------------------
def time_series_chart(
    df_telemetry: pd.DataFrame,
    df_predictions: Optional[pd.DataFrame] = None,
    window_minutes: int = 60,
) -> go.Figure:
    """Dual-axis plot: temp/humidity lines + CO2 secondary + motion shaded + risk overlay."""
    df = df_telemetry.copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="No telemetry yet — wait for simulator to publish first windows.")
        return fig

    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.70, 0.30],
        subplot_titles=("Temperature / Humidity / CO2 (last %d min)" % window_minutes, "Motion + Risk"),
    )

    # Temp
    fig.add_trace(
        go.Scatter(
            x=df["dt"], y=df["temperature"],
            name="Temp (°C)", mode="lines",
            line=dict(color="#e74c3c", width=2),
            yaxis="y1",
        ),
        row=1, col=1,
    )
    # Humidity
    fig.add_trace(
        go.Scatter(
            x=df["dt"], y=df["humidity"],
            name="Humidity (%)", mode="lines",
            line=dict(color="#3498db", width=2),
            yaxis="y1",
        ),
        row=1, col=1,
    )
    # CO2 on a secondary y-axis (row 1 still).
    fig.add_trace(
        go.Scatter(
            x=df["dt"], y=df["co2"],
            name="CO2 (ppm)", mode="lines",
            line=dict(color="#27ae60", width=2, dash="dot"),
            yaxis="y2",
        ),
        row=1, col=1,
    )

    # Shade motion = 1 regions in row 2.
    if "motion" in df.columns:
        df_m = df.set_index("dt")["motion"]
        # Contiguous runs by grouping changes.
        groups = (df_m.diff().fillna(0) != 0).cumsum()
        for _, grp in df_m.groupby(groups):
            if grp.iloc[0] != 1:
                continue
            lo = grp.index.min()
            hi = grp.index.max()
            fig.add_vrect(
                x0=lo, x1=hi,
                fillcolor="rgba(241, 196, 15, 0.18)",
                line_width=0,
                annotation_text="",
                row=2, col=1,
            )
        # Motion line itself (always 0/1) for a reference.
        fig.add_trace(
            go.Scatter(
                x=df["dt"], y=df["motion"],
                name="Motion (PIR)", mode="lines",
                line=dict(color="#f39c12", width=2, shape="hv"),
                fill="tozeroy",
                fillcolor="rgba(243,156,18,0.15)",
            ),
            row=2, col=1,
        )

    # Predictions overlay.
    if df_predictions is not None and not df_predictions.empty:
        dfp = df_predictions.copy()
        dfp["dt"] = pd.to_datetime(dfp["ts"], unit="ms", utc=True).dt.tz_convert(None)
        risk_map = {"low": 0.1, "medium": 0.5, "high": 1.0}
        dfp["risk_num"] = dfp["risk_level"].map(risk_map).fillna(0)
        color_map = {"low": "#2ecc71", "medium": "#f1c40f", "high": "#e74c3c"}
        for label, color in color_map.items():
            seg = dfp[dfp["risk_level"] == label]
            if seg.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=seg["dt"], y=seg["risk_num"],
                    name=f"Risk={label}", mode="markers",
                    marker=dict(color=color, size=7, symbol="diamond"),
                ),
                row=2, col=1,
            )

    fig.update_yaxes(title_text="Temp (°C) / Hum (%)", row=1, col=1, side="left")
    fig.update_layout(
        yaxis2=dict(
            title="CO2 (ppm)", overlaying="y", side="right",
            showgrid=False, rangemode="tozero",
        ),
    )
    fig.update_yaxes(title_text="Motion / Risk", row=2, col=1, range=[-0.1, 1.2], tickvals=[0, 0.5, 1])
    fig.update_xaxes(title_text="Time (UTC)", row=2, col=1)

    fig.update_layout(
        height=620,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="left", x=0),
        margin=dict(l=40, r=40, t=60, b=10),
        hovermode="x unified",
        template="plotly_white",
    )
    return fig


# ---------------------------------------------------------------------------
# Risk badge (HTML for st.markdown unsafe_allow_html=True).
# ---------------------------------------------------------------------------
def risk_badge(risk_level: str) -> str:
    """Return a Streamlit-markdown-safe HTML badge string for a risk level."""
    rl = (risk_level or "low").lower()
    color = {
        "low": "#2ecc71",
        "medium": "#f1c40f",
        "high": "#e74c3c",
    }.get(rl, "#95a5a6")
    text = {
        "low": "LOW &nbsp;·&nbsp; All clear",
        "medium": "MEDIUM &nbsp;·&nbsp; Occupied, air quality OK",
        "high": "HIGH &nbsp;·&nbsp; Actuate ventilation",
    }.get(rl, rl.upper())
    return (
        f"<span style='display:inline-block;padding:6px 16px;border-radius:10px;"
        f"background:{color};color:white;font-weight:600;font-size:1.1em;"
        f"box-shadow:0 1px 2px rgba(0,0,0,0.15)'>{text}</span>"
    )


def risk_history_sparkline(
    df_predictions: Optional[pd.DataFrame],
    last_n: int = 60,
) -> go.Figure:
    """A small horizontal strip chart of recent risk levels."""
    if df_predictions is None or df_predictions.empty:
        fig = go.Figure()
        fig.update_layout(title="No predictions yet.", height=120, margin=dict(l=10, r=10, t=30, b=10))
        return fig
    dfp = df_predictions.copy().tail(last_n)
    dfp["dt"] = pd.to_datetime(dfp["ts"], unit="ms", utc=True).dt.tz_convert(None)
    risk_map = {"low": 0, "medium": 1, "high": 2}
    color_map = {"low": "#2ecc71", "medium": "#f1c40f", "high": "#e74c3c"}
    dfp["risk_num"] = dfp["risk_level"].map(risk_map).fillna(0)
    dfp["color"] = dfp["risk_level"].map(color_map).fillna("#95a5a6")
    fig = go.Figure(
        go.Scatter(
            x=dfp["dt"], y=dfp["risk_num"],
            mode="markers+lines",
            line=dict(shape="hv", color="gray", width=1),
            marker=dict(color=dfp["color"], size=8, line=dict(width=0)),
        )
    )
    fig.update_layout(
        height=140,
        margin=dict(l=10, r=10, t=20, b=30),
        yaxis=dict(
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=["Low", "Med", "High"],
            range=[-0.3, 2.3],
        ),
        template="plotly_white",
    )
    return fig
