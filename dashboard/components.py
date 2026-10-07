"""Reusable Plotly chart, gauge, and UI component helpers for Aegis.

No Streamlit UI code here — only pure Plotly Figure builders and HTML generators
so they can be unit-tested or reused outside Streamlit.
"""

from __future__ import annotations

import html
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Theme Colors & Layout Defaults (Dark Mode)
# ---------------------------------------------------------------------------
THEME_BG = "#0b0f19"          # Deep slate near-black
THEME_PAPER = "#0f172a"       # Slate-900 surface
THEME_GRID = "rgba(255, 255, 255, 0.06)"
THEME_BORDER = "rgba(255, 255, 255, 0.10)"
COLOR_ACCENT = "#00e5ff"      # Electric Teal / Cyan
COLOR_TEMP = "#38bdf8"        # Sky Blue
COLOR_HUMID = "#818cf8"       # Indigo / Purple
COLOR_CO2 = "#34d399"         # Mint Emerald
COLOR_WARN = "#f59e0b"        # Amber
COLOR_ALERT = "#ef4444"       # Red
COLOR_MUTED = "#94a3b8"       # Muted Slate


def _base_dark_layout(height: int = 380) -> dict:
    """Return common dark Plotly layout dict."""
    return dict(
        height=height,
        paper_bgcolor=THEME_BG,
        plot_bgcolor=THEME_BG,
        margin=dict(l=45, r=45, t=35, b=35),
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            color=COLOR_MUTED,
            size=12,
        ),
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_color="#f8fafc",
            font_size=12,
            bordercolor="#334155",
        ),
    )


# ---------------------------------------------------------------------------
# Radial Gauge Indicator (Preserved & Enhanced)
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
    """A polished dark-theme radial indicator gauge with threshold zones."""
    value = float(value) if not pd.isna(value) else float(min_v)
    value = float(np.clip(value, min_v, max_v))

    steps = []
    if danger_threshold is not None:
        if warning_threshold is None:
            warning_threshold = danger_threshold - 0.2 * (max_v - min_v)
        if not lower_is_bad:
            steps = [
                {"range": [min_v, warning_threshold], "color": "rgba(16, 185, 129, 0.25)"},
                {"range": [warning_threshold, danger_threshold], "color": "rgba(245, 158, 11, 0.35)"},
                {"range": [danger_threshold, max_v], "color": "rgba(239, 68, 68, 0.45)"},
            ]
        else:
            steps = [
                {"range": [min_v, danger_threshold], "color": "rgba(239, 68, 68, 0.45)"},
                {"range": [danger_threshold, warning_threshold], "color": "rgba(245, 158, 11, 0.35)"},
                {"range": [warning_threshold, max_v], "color": "rgba(16, 185, 129, 0.25)"},
            ]
    else:
        steps = [{"range": [min_v, max_v], "color": "rgba(0, 229, 255, 0.20)"}]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={
                "text": f"<b>{html.escape(label)}</b><br><span style='font-size:0.7em;color:{COLOR_MUTED}'>{html.escape(unit)}</span>",
                "font": {"color": "#f8fafc", "size": 15},
            },
            gauge={
                "axis": {
                    "range": [min_v, max_v],
                    "tickcolor": COLOR_MUTED,
                    "tickwidth": 1,
                    "tickfont": {"color": COLOR_MUTED, "size": 10},
                },
                "bar": {"color": COLOR_ACCENT, "thickness": 0.30},
                "bgcolor": "#1e293b",
                "borderwidth": 1,
                "bordercolor": THEME_BORDER,
                "steps": steps,
                "threshold": {
                    "line": {"color": "#ffffff", "width": 2},
                    "thickness": 0.75,
                    "value": value,
                },
            },
            number={
                "font": {"size": 34, "color": "#f8fafc", "family": "monospace"},
                "valueformat": ".1f",
            },
        )
    )
    layout = _base_dark_layout(height=240)
    layout["margin"] = dict(l=25, r=25, t=45, b=25)
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Main Rolling Time-Series Chart
# ---------------------------------------------------------------------------
def time_series_chart(
    df_telemetry: pd.DataFrame,
    df_predictions: Optional[pd.DataFrame] = None,
    window_minutes: int = 60,
) -> go.Figure:
    """Dual-axis interactive Plotly chart with dark theme matching Aegis."""
    if df_telemetry.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Waiting for sensor telemetry from simulator...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=COLOR_MUTED, size=14),
        )
        layout = _base_dark_layout(height=380)
        fig.update_layout(**layout)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    df = df_telemetry.copy()
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)

    fig = go.Figure()

    # Temperature Trace (Left Axis)
    fig.add_trace(
        go.Scatter(
            x=df["dt"],
            y=df["temperature"],
            name="Temperature (°C)",
            mode="lines",
            line=dict(color=COLOR_TEMP, width=2.4),
            yaxis="y1",
            hovertemplate="Temp: <b>%{y:.2f} °C</b><extra></extra>",
        )
    )

    # Humidity Trace (Left Axis)
    fig.add_trace(
        go.Scatter(
            x=df["dt"],
            y=df["humidity"],
            name="Humidity (%)",
            mode="lines",
            line=dict(color=COLOR_HUMID, width=2.0),
            yaxis="y1",
            hovertemplate="Humidity: <b>%{y:.1f} %</b><extra></extra>",
        )
    )

    # CO2 Trace (Right Axis)
    fig.add_trace(
        go.Scatter(
            x=df["dt"],
            y=df["co2"],
            name="CO₂ (ppm)",
            mode="lines",
            line=dict(color=COLOR_CO2, width=2.2, dash="solid"),
            yaxis="y2",
            hovertemplate="CO₂: <b>%{y:.0f} ppm</b><extra></extra>",
        )
    )

    # CO2 1000 ppm Reference line (Action / High Risk Threshold)
    max_co2 = float(df["co2"].max()) if not df["co2"].isna().all() else 800.0
    if max_co2 >= 700:
        fig.add_hline(
            y=1000,
            yref="y2",
            line_dash="dot",
            line_color="rgba(239, 68, 68, 0.65)",
            line_width=1.5,
            annotation_text="CO₂ Risk Threshold (1000 ppm)",
            annotation_position="top right",
            annotation_font=dict(color=COLOR_ALERT, size=10),
        )

    # Overlay Risk Badges / markers if predictions exist
    if df_predictions is not None and not df_predictions.empty:
        dfp = df_predictions.copy()
        dfp["dt"] = pd.to_datetime(dfp["ts"], unit="ms", utc=True).dt.tz_convert(None)
        high_preds = dfp[dfp["risk_level"] == "high"]
        if not high_preds.empty:
            # Map high risk points onto the telemetry timestamps if within range
            fig.add_trace(
                go.Scatter(
                    x=high_preds["dt"],
                    y=[1000] * len(high_preds),
                    name="High Risk Event",
                    mode="markers",
                    yaxis="y2",
                    marker=dict(
                        symbol="triangle-up",
                        size=9,
                        color=COLOR_ALERT,
                        line=dict(color="#ffffff", width=1),
                    ),
                    hovertemplate="<b>HIGH RISK CLASSIFIED</b><extra></extra>",
                )
            )

    layout = _base_dark_layout(height=400)
    layout.update(
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0, 0, 0, 0)",
            font=dict(color=COLOR_MUTED, size=11),
        ),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor=THEME_GRID,
            zeroline=False,
            showline=True,
            linecolor=THEME_BORDER,
            tickformat="%H:%M:%S",
            tickfont=dict(color=COLOR_MUTED, size=11),
        ),
        yaxis=dict(
            title="Temp (°C) / Humidity (%)",
            title_font=dict(color=COLOR_MUTED, size=11),
            showgrid=True,
            gridcolor=THEME_GRID,
            zeroline=False,
            showline=True,
            linecolor=THEME_BORDER,
            tickfont=dict(color=COLOR_MUTED, size=11),
            side="left",
        ),
        yaxis2=dict(
            title="CO₂ (ppm)",
            title_font=dict(color=COLOR_CO2, size=11),
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor=THEME_BORDER,
            tickfont=dict(color=COLOR_CO2, size=11),
        ),
    )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Occupancy / Motion Horizontal Timeline Strip Chart
# ---------------------------------------------------------------------------
def motion_timeline_chart(
    df_telemetry: pd.DataFrame,
    window_minutes: int = 60,
) -> go.Figure:
    """A compact horizontal strip chart showing motion events over time."""
    if df_telemetry.empty or "motion" not in df_telemetry.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Waiting for motion sensor readings...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=COLOR_MUTED, size=12),
        )
        layout = _base_dark_layout(height=110)
        fig.update_layout(**layout)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    df = df_telemetry.copy()
    df["dt"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert(None)

    fig = go.Figure()

    # Shaded stepped ribbon for motion status
    fig.add_trace(
        go.Scatter(
            x=df["dt"],
            y=df["motion"],
            name="PIR Motion",
            mode="lines",
            line=dict(color=COLOR_ACCENT, width=1.8, shape="hv"),
            fill="tozeroy",
            fillcolor="rgba(0, 229, 255, 0.18)",
            customdata=["Motion Detected" if m else "Clear / Idle" for m in df["motion"]],
            hovertemplate="Occupancy: <b>%{customdata}</b> (%{x|%H:%M:%S})<extra></extra>",
        )
    )

    # Highlight active points with glowing markers
    active = df[df["motion"] == 1]
    if not active.empty:
        fig.add_trace(
            go.Scatter(
                x=active["dt"],
                y=active["motion"],
                name="Active Event",
                mode="markers",
                marker=dict(
                    color=COLOR_ACCENT,
                    size=6,
                    line=dict(color="#ffffff", width=1),
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    layout = _base_dark_layout(height=120)
    layout["margin"] = dict(l=45, r=45, t=10, b=25)
    layout.update(
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor=THEME_GRID,
            zeroline=False,
            showline=True,
            linecolor=THEME_BORDER,
            tickformat="%H:%M:%S",
            tickfont=dict(color=COLOR_MUTED, size=10),
            # Align time range with the main chart
            range=[df["dt"].min(), df["dt"].max()] if len(df) > 1 else None,
        ),
        yaxis=dict(
            title="Occupancy",
            title_font=dict(color=COLOR_MUTED, size=10),
            tickmode="array",
            tickvals=[0, 1],
            ticktext=["Clear", "Active"],
            tickfont=dict(color=COLOR_MUTED, size=9),
            range=[-0.15, 1.25],
            showgrid=False,
            zeroline=False,
            showline=True,
            linecolor=THEME_BORDER,
        ),
    )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# Risk History Sparkline
# ---------------------------------------------------------------------------
def risk_history_sparkline(
    df_predictions: Optional[pd.DataFrame],
    last_n: int = 60,
) -> go.Figure:
    """A small horizontal strip chart of recent ML risk predictions."""
    if df_predictions is None or df_predictions.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No prediction history yet.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(color=COLOR_MUTED, size=11),
        )
        layout = _base_dark_layout(height=130)
        fig.update_layout(**layout)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    dfp = df_predictions.copy().tail(last_n)
    dfp["dt"] = pd.to_datetime(dfp["ts"], unit="ms", utc=True).dt.tz_convert(None)

    risk_map = {"low": 0, "medium": 1, "high": 2}
    color_map = {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"}
    dfp["risk_num"] = dfp["risk_level"].map(risk_map).fillna(0)
    dfp["color"] = dfp["risk_level"].map(color_map).fillna(COLOR_MUTED)

    fig = go.Figure(
        go.Scatter(
            x=dfp["dt"],
            y=dfp["risk_num"],
            mode="markers+lines",
            line=dict(shape="hv", color="rgba(255, 255, 255, 0.20)", width=1.5),
            marker=dict(color=dfp["color"], size=7, line=dict(width=0)),
            customdata=dfp["risk_level"].str.upper(),
            hovertemplate="Risk: <b>%{customdata}</b> (%{x|%H:%M:%S})<extra></extra>",
        )
    )

    layout = _base_dark_layout(height=130)
    layout["margin"] = dict(l=35, r=25, t=15, b=25)
    layout.update(
        showlegend=False,
        hovermode="closest",
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor=THEME_GRID,
            tickformat="%H:%M:%S",
            tickfont=dict(color=COLOR_MUTED, size=9),
            showline=True,
            linecolor=THEME_BORDER,
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=["Low", "Med", "High"],
            tickfont=dict(color=COLOR_MUTED, size=10),
            range=[-0.35, 2.35],
            showgrid=True,
            gridcolor=THEME_GRID,
            showline=True,
            linecolor=THEME_BORDER,
        ),
    )
    fig.update_layout(**layout)
    return fig


# ---------------------------------------------------------------------------
# KPI Card Status Badges (HTML)
# ---------------------------------------------------------------------------
def kpi_status_badge(metric_name: str, value: float) -> str:
    """Return an HTML badge indicating whether the value is in a healthy range."""
    if pd.isna(value):
        return "<span class='kpi-badge badge-neutral'>— No Data</span>"

    if metric_name == "temperature":
        t = float(value)
        if 18.0 <= t <= 25.0:
            return "<span class='kpi-badge badge-normal'>● Optimal (18–25°C)</span>"
        elif 25.0 < t <= 26.5:
            return "<span class='kpi-badge badge-warning'>▲ Elevated (25–26.5°C)</span>"
        elif t > 26.5:
            return "<span class='kpi-badge badge-alert'>▲ High Risk (>26.5°C)</span>"
        else:
            return "<span class='kpi-badge badge-warning'>▼ Below Range (<18°C)</span>"

    elif metric_name == "humidity":
        h = float(value)
        if 30.0 <= h <= 60.0:
            return "<span class='kpi-badge badge-normal'>● Optimal (30–60%)</span>"
        elif 60.0 < h <= 68.0:
            return "<span class='kpi-badge badge-warning'>▲ Elevated (60–68%)</span>"
        elif h > 68.0:
            return "<span class='kpi-badge badge-alert'>▲ High (>68%)</span>"
        else:
            return "<span class='kpi-badge badge-alert'>▼ Dry Air (<30%)</span>"

    elif metric_name == "co2":
        c = float(value)
        if c < 800:
            return "<span class='kpi-badge badge-normal'>● Fresh Air (<800 ppm)</span>"
        elif 800 <= c < 1000:
            return "<span class='kpi-badge badge-warning'>▲ Elevated (800–1000)</span>"
        else:
            return "<span class='kpi-badge badge-alert'>▲ Poor Air (≥1000 ppm)</span>"

    elif metric_name == "motion":
        m = int(value)
        if m == 1:
            return "<span class='kpi-badge badge-accent'>● Active Occupancy</span>"
        else:
            return "<span class='kpi-badge badge-muted'>○ Clear / Idle</span>"

    return "<span class='kpi-badge badge-neutral'>Normal</span>"


# ---------------------------------------------------------------------------
# Risk Panel Badge & Card Component (HTML)
# ---------------------------------------------------------------------------
def risk_badge(
    risk_level: str,
    confidence: Optional[float] = None,
    model_version: Optional[str] = "random_forest_v1",
    probabilities: Optional[Dict[str, float]] = None,
) -> str:
    """Return a styled HTML badge and details card for current ML risk."""
    rl = (risk_level or "low").lower()

    styles = {
        "low": {
            "border": "#10b981",
            "bg": "rgba(16, 185, 129, 0.12)",
            "text": "#34d399",
            "title": "LOW RISK · Optimal Environment",
            "desc": "Room parameters indicate an unoccupied or well-ventilated space. Air exchange is optimal.",
            "icon": "🛡️",
        },
        "medium": {
            "border": "#f59e0b",
            "bg": "rgba(245, 158, 11, 0.14)",
            "text": "#fbbf24",
            "title": "MODERATE RISK · Occupied / CO₂ Rising",
            "desc": "Occupancy detected with rising CO₂. Telemetry remains within acceptable indoor safety thresholds.",
            "icon": "⚠️",
        },
        "high": {
            "border": "#ef4444",
            "bg": "rgba(239, 68, 68, 0.18)",
            "text": "#f87171",
            "title": "HIGH RISK · Actuate Ventilation",
            "desc": "Air quality threshold exceeded (CO₂ ≥ 1000 ppm or Temp ≥ 26°C). Automated simulated ventilation initiated.",
            "icon": "🚨",
        },
    }
    cfg = styles.get(rl, styles["low"])

    conf_text = ""
    if confidence is not None:
        conf_pct = float(confidence) * 100.0 if float(confidence) <= 1.0 else float(confidence)
        conf_text = f"<span class='risk-confidence-pill'>Confidence: <b>{conf_pct:.1f}%</b></span>"

    # Probabilities bar breakdown if provided
    prob_bars_html = ""
    if probabilities:
        p_low = probabilities.get("low", 0.0) * 100
        p_med = probabilities.get("medium", 0.0) * 100
        p_high = probabilities.get("high", 0.0) * 100
        prob_bars_html = f"""
        <div class='risk-proba-container'>
            <div class='risk-proba-labels'>
                <span>Low: <b>{p_low:.0f}%</b></span>
                <span>Med: <b>{p_med:.0f}%</b></span>
                <span>High: <b>{p_high:.0f}%</b></span>
            </div>
            <div class='risk-proba-bar-track'>
                <div class='risk-bar-low' style='width: {p_low:.1f}%'></div>
                <div class='risk-bar-med' style='width: {p_med:.1f}%'></div>
                <div class='risk-bar-high' style='width: {p_high:.1f}%'></div>
            </div>
        </div>
        """

    return f"""
    <div class='risk-card' style='border-color: {cfg["border"]}; background: {cfg["bg"]};'>
        <div class='risk-header'>
            <div class='risk-badge-pill' style='background: {cfg["border"]}; color: #ffffff;'>
                <span>{cfg["icon"]}</span>
                <span>{rl.upper()} RISK</span>
            </div>
            {conf_text}
            <span class='risk-version-tag'>model: <code>{html.escape(model_version or "v1")}</code></span>
        </div>
        <div class='risk-title-text' style='color: {cfg["text"]};'>
            {cfg["title"]}
        </div>
        <div class='risk-description'>
            {cfg["desc"]}
        </div>
        {prob_bars_html}
    </div>
    """


# ---------------------------------------------------------------------------
# Actuation Log Activity Feed Component (HTML)
# ---------------------------------------------------------------------------
def render_actuation_feed(df_actuations: pd.DataFrame, limit: int = 50) -> str:
    """Return a scrollable HTML activity feed for simulated actuation events."""
    if df_actuations.empty:
        return """
        <div class='actuation-feed-box'>
            <div class='sim-watermark'>
                <span class='sim-pill'>SIMULATED LOG</span>
                <span>Software emulation only · No physical relays or actuators</span>
            </div>
            <div class='feed-empty-state'>
                <p>No actuation events recorded yet.</p>
                <small>Simulated actions (e.g., <code>VENTILATION_ON</code>) trigger automatically when the ML classifier predicts sustained HIGH risk.</small>
            </div>
        </div>
        """

    df = df_actuations.copy().tail(limit)
    # Order most recent first
    df = df.iloc[::-1].reset_index(drop=True)

    items_html = []
    for _, row in df.iterrows():
        action = str(row.get("action", "UNKNOWN"))
        room = str(row.get("room", "room1"))
        reason = html.escape(str(row.get("reason", "")))
        ts = int(row.get("ts", 0))

        if ts > 0:
            when = pd.to_datetime(ts, unit="ms", utc=True).strftime("%H:%M:%S UTC")
        else:
            when = "—"

        # Action tag style
        if "VENTILATION_ON" in action:
            badge_class = "action-vent-on"
            icon = "🌀"
        elif "HVAC_COOL_ON" in action:
            badge_class = "action-cool-on"
            icon = "❄️"
        elif "VENTILATION_OFF" in action:
            badge_class = "action-vent-off"
            icon = "⏹️"
        else:
            badge_class = "action-default"
            icon = "⚡"

        items_html.append(f"""
        <div class='activity-row'>
            <div class='activity-icon'>{icon}</div>
            <div class='activity-details'>
                <div class='activity-headline'>
                    <span class='action-badge {badge_class}'>{html.escape(action)}</span>
                    <span class='activity-room'>{html.escape(room)}</span>
                    <span class='activity-time'>{when}</span>
                </div>
                <div class='activity-reason'>{reason}</div>
            </div>
        </div>
        """)

    feed_items = "\n".join(items_html)

    return f"""
    <div class='actuation-feed-box'>
        <div class='sim-watermark'>
            <span class='sim-pill'>SIMULATED LOG</span>
            <span>No real hardware is actuated · AIoT automation pipeline demonstration</span>
        </div>
        <div class='activity-scroll-area'>
            {feed_items}
        </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Top Bar HUD Component (HTML)
# ---------------------------------------------------------------------------
def render_top_bar(
    room_name: str,
    latest_ts: Optional[int],
    is_stale: bool,
    stale_minutes: float,
) -> str:
    """Return top bar HUD HTML with branding, room, timestamp, and status dot."""
    if latest_ts is not None and latest_ts > 0:
        time_str = pd.to_datetime(latest_ts, unit="ms", utc=True).strftime("%H:%M:%S UTC")
        if stale_minutes < 1.0:
            age_str = "just now"
        elif stale_minutes < 60:
            age_str = f"{stale_minutes:.1f}m ago"
        else:
            age_str = f"{stale_minutes/60:.1f}h ago"
        sync_label = f"Latest Reading: <b>{time_str}</b> ({age_str})"
    else:
        sync_label = "Awaiting first reading..."

    if is_stale or latest_ts is None:
        status_dot_class = "dot-stale"
        status_text = "Stale Pipeline (>5m)" if is_stale else "Disconnected"
    else:
        status_dot_class = "dot-healthy"
        status_text = "Pipeline Healthy"

    return f"""
    <div class='aegis-topbar'>
        <div class='topbar-brand'>
            <div class='shield-icon-wrapper'>
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="{COLOR_ACCENT}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    <circle cx="12" cy="11" r="2.8" fill="{COLOR_ACCENT}" fill-opacity="0.25"/>
                </svg>
            </div>
            <div class='brand-text'>
                <div class='brand-title'>Aegis <span class='brand-sub'>Room Intelligence</span></div>
                <div class='brand-tagline'>See what matters. Nothing more.</div>
            </div>
        </div>
        <div class='topbar-status'>
            <div class='room-badge'>ROOM: <b>{html.escape(room_name)}</b></div>
            <div class='sync-timestamp'>{sync_label}</div>
            <div class='status-pill'>
                <span class='status-dot {status_dot_class}'></span>
                <span class='status-text'>{status_text}</span>
            </div>
        </div>
    </div>
    """
