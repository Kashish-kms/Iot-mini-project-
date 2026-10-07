"""Aegis — Privacy-Aware Room Intelligence Dashboard.

Live telemetry and ML-based indoor environmental risk monitoring.
Designed with strict privacy-by-design principles: only 1-minute aggregated
telemetry is displayed; raw high-frequency sensor readings never leave the simulator.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import dotenv
import joblib
import pandas as pd
import streamlit as st

# Setup module paths
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ingestion import database as db
    from dashboard.components import (
        gauge,
        kpi_status_badge,
        motion_timeline_chart,
        render_actuation_feed,
        render_top_bar,
        risk_badge,
        risk_history_sparkline,
        time_series_chart,
    )
    from ml.train import FEATURE_COLUMNS, _select_X
else:
    from ingestion import database as db
    from .components import (
        gauge,
        kpi_status_badge,
        motion_timeline_chart,
        render_actuation_feed,
        render_top_bar,
        risk_badge,
        risk_history_sparkline,
        time_series_chart,
    )
    from ml.train import FEATURE_COLUMNS, _select_X

dotenv.load_dotenv()

# Configuration from environment
REFRESH_SEC = int(os.environ.get("REFRESH_SEC", "10"))
DB_PATH = os.environ.get("DB_PATH", "./data/iot.db")
DEFAULT_WINDOW_MIN = int(os.environ.get("DASH_WINDOW_MIN", "60"))
ROOM_DEFAULT = os.environ.get("ROOM_ID", "room1")

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "models"
MODEL_VERSION = "random_forest_v1"
MODEL_PATH = MODEL_DIR / f"{MODEL_VERSION}.joblib"

# ---------------------------------------------------------------------------
# Streamlit Page Setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Aegis — Privacy-Aware Room Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for Aegis Brand & Dark HUD Aesthetic
# ---------------------------------------------------------------------------
AEGIS_CUSTOM_CSS = """
<style>
/* Base Dark Theme Overrides */
.stApp {
    background-color: #080c14;
    color: #f8fafc;
}

/* Hide default streamlit decorations */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Container & Block adjustments */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 96% !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #0b0f19;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
    margin: 1rem 0;
}

/* Aegis Top Bar HUD */
.aegis-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 22px;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
}
.topbar-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}
.shield-icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    border-radius: 10px;
    background: rgba(0, 229, 255, 0.08);
    border: 1px solid rgba(0, 229, 255, 0.25);
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.15);
}
.brand-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.02em;
    display: flex;
    align-items: baseline;
    gap: 8px;
}
.brand-sub {
    font-size: 0.85rem;
    font-weight: 500;
    color: #00e5ff;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.brand-tagline {
    font-size: 0.82rem;
    color: #94a3b8;
    margin-top: 2px;
    font-style: italic;
}
.topbar-status {
    display: flex;
    align-items: center;
    gap: 16px;
}
.room-badge {
    background: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.10);
    padding: 5px 12px;
    border-radius: 6px;
    font-size: 0.82rem;
    color: #cbd5e1;
}
.room-badge b {
    color: #00e5ff;
}
.sync-timestamp {
    font-size: 0.82rem;
    color: #94a3b8;
}
.sync-timestamp b {
    color: #f1f5f9;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 12px;
    border-radius: 20px;
    background: #1e293b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 0.82rem;
    font-weight: 600;
}
.status-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
}
.dot-healthy {
    background-color: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse-green 2s infinite;
}
.dot-stale {
    background-color: #ef4444;
    box-shadow: 0 0 8px #ef4444;
    animation: pulse-red 2s infinite;
}
@keyframes pulse-green {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
@keyframes pulse-red {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
    70% { transform: scale(1.05); box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

/* Stale Warning Banner */
.stale-warning-banner {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(239, 68, 68, 0.12);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 1rem;
    color: #fca5a5;
    font-size: 0.88rem;
}

/* Empty State Card */
.empty-state-card {
    background: #0f172a;
    border: 1px dashed rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 3rem 2rem;
    text-align: center;
    margin: 1.5rem 0;
}
.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 0.8rem;
}
.empty-state-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 0.4rem;
}
.empty-state-desc {
    font-size: 0.9rem;
    color: #94a3b8;
    max-width: 500px;
    margin: 0 auto;
}

/* Metric Cards Styling */
div[data-testid="stMetric"] {
    background-color: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px 18px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    transition: transform 0.15s ease, border-color 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(0, 229, 255, 0.4);
    transform: translateY(-2px);
}
div[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    font-family: ui-monospace, Menlo, Monaco, 'Courier New', monospace;
}

/* KPI Badges */
.kpi-badge {
    display: inline-block;
    margin-top: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}
.badge-normal {
    background: rgba(16, 185, 129, 0.14);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.badge-warning {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
}
.badge-alert {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
}
.badge-accent {
    background: rgba(0, 229, 255, 0.12);
    color: #00e5ff;
    border: 1px solid rgba(0, 229, 255, 0.3);
}
.badge-muted {
    background: rgba(148, 163, 184, 0.12);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.2);
}
.badge-neutral {
    background: rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Section Headers */
.section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 1.4rem;
    margin-bottom: 0.5rem;
}
.section-title {
    font-size: 1.02rem;
    font-weight: 600;
    color: #e2e8f0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-subtitle {
    font-size: 0.78rem;
    color: #64748b;
}

/* Risk Card Component */
.risk-card {
    border: 1px solid;
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 0.8rem;
}
.risk-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    flex-wrap: wrap;
}
.risk-badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.risk-confidence-pill {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.76rem;
    color: #e2e8f0;
}
.risk-version-tag {
    font-size: 0.74rem;
    color: #64748b;
    margin-left: auto;
}
.risk-version-tag code {
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 5px;
    border-radius: 4px;
}
.risk-title-text {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 4px;
}
.risk-description {
    font-size: 0.83rem;
    color: #94a3b8;
    line-height: 1.45;
}
.risk-proba-container {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.risk-proba-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: #94a3b8;
    margin-bottom: 4px;
}
.risk-proba-bar-track {
    display: flex;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.06);
}
.risk-bar-low { background-color: #10b981; }
.risk-bar-med { background-color: #f59e0b; }
.risk-bar-high { background-color: #ef4444; }

/* Actuation Activity Feed Component */
.actuation-feed-box {
    background: #0f172a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
}
.sim-watermark {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.73rem;
    color: #64748b;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 10px;
}
.sim-pill {
    background: rgba(0, 229, 255, 0.12);
    color: #00e5ff;
    border: 1px solid rgba(0, 229, 255, 0.25);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 0.68rem;
    font-weight: 700;
}
.activity-scroll-area {
    max-height: 255px;
    overflow-y: auto;
    padding-right: 4px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.activity-scroll-area::-webkit-scrollbar {
    width: 5px;
}
.activity-scroll-area::-webkit-scrollbar-track {
    background: #0b0f19;
}
.activity-scroll-area::-webkit-scrollbar-thumb {
    background: #334155;
    border-radius: 3px;
}
.activity-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 6px;
}
.activity-icon {
    font-size: 1rem;
    margin-top: 1px;
}
.activity-details {
    flex: 1;
}
.activity-headline {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 3px;
}
.action-badge {
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: ui-monospace, monospace;
}
.action-vent-on {
    background: rgba(0, 229, 255, 0.15);
    color: #00e5ff;
    border: 1px solid rgba(0, 229, 255, 0.35);
}
.action-cool-on {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
}
.action-vent-off {
    background: rgba(148, 163, 184, 0.15);
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.3);
}
.action-default {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
.activity-room {
    font-size: 0.72rem;
    color: #64748b;
}
.activity-time {
    font-size: 0.72rem;
    color: #94a3b8;
    margin-left: auto;
}
.activity-reason {
    font-size: 0.78rem;
    color: #cbd5e1;
    line-height: 1.35;
}
.feed-empty-state {
    padding: 1.8rem 1rem;
    text-align: center;
    color: #94a3b8;
}
.feed-empty-state p {
    font-size: 0.88rem;
    margin-bottom: 4px;
    color: #cbd5e1;
}
.feed-empty-state small {
    font-size: 0.75rem;
    color: #64748b;
}

/* Privacy Expander Styling */
div[data-testid="stExpander"] {
    background: #0f172a !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
}
</style>
"""
st.markdown(AEGIS_CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Database & Model Caching Helpers
# ---------------------------------------------------------------------------
def _ensure_conn():
    try:
        return db.init_db(DB_PATH)
    except Exception as exc:
        st.error(f"Failed to connect to SQLite at {DB_PATH}: {exc}")
        return None


@st.cache_resource(show_spinner=False)
def _load_latest_model():
    if not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _predict_risk_and_infer(
    conn, latest_ts: Optional[int], window_min: int
) -> Tuple[str, Optional[float], Dict[str, float]]:
    """Predict risk level with confidence & probability using RandomForest."""
    if conn is None:
        return "low", None, {}

    model = _load_latest_model()
    features = db.query_all_features(conn)

    # If no features or no model, fall back to recent prediction in DB
    if model is None or features.empty:
        preds = db.query_recent_predictions(conn, minutes=window_min * 2)
        if not preds.empty:
            return str(preds["risk_level"].iloc[-1]), None, {}
        return "low", None, {}

    X_all = _select_X(features)
    if X_all.empty:
        return "low", None, {}

    last_row_df = X_all.iloc[[-1]].copy()
    ts_row = int(features["ts"].iloc[-1])

    # Classify
    pred = str(model.predict(last_row_df)[0])

    confidence = None
    probabilities: Dict[str, float] = {}
    if hasattr(model, "predict_proba"):
        try:
            probas = model.predict_proba(last_row_df)[0]
            classes = list(getattr(model, "classes_", ["high", "low", "medium"]))
            probabilities = {str(c): float(p) for c, p in zip(classes, probas)}
            confidence = float(probabilities.get(pred, max(probas)))
        except Exception:
            pass

    # Save to SQLite predictions table if not redundant
    target_ts = latest_ts if latest_ts and latest_ts > 10_000_000_000 else int(time.time() * 1000)
    try:
        preds = db.query_recent_predictions(conn, minutes=5)
        if preds.empty or int(preds["ts"].iloc[-1]) < target_ts:
            db.insert_prediction(conn, target_ts, pred, MODEL_VERSION)
    except Exception:
        pass

    return pred, confidence, probabilities


def _simulate_actuation(conn, risk_now: str, prev_risk: Optional[str], room: str) -> None:
    """SIMULATED actuation activity logger. No physical hardware is actuated.

    Rules:
      - risk transitions low/medium → high  → VENTILATION_ON
      - stays high 2+ consecutive reads     → HVAC_COOL_ON if temp >= 24.5°C
      - transitions high → low/medium       → VENTILATION_OFF
    """
    if conn is None or risk_now is None:
        return

    now_ts = int(time.time() * 1000)

    st.session_state.setdefault("_high_streak", 0)
    st.session_state.setdefault("_last_risk", prev_risk)

    if risk_now == "high":
        st.session_state["_high_streak"] = int(st.session_state["_high_streak"]) + 1
    else:
        st.session_state["_high_streak"] = 0

    streak = st.session_state["_high_streak"]
    prev = st.session_state.get("_last_risk")

    telem = db.query_recent_telemetry(conn, minutes=5)
    temp_now = float(telem["temperature"].iloc[-1]) if not telem.empty else 22.0

    action = reason = None
    if prev != "high" and risk_now == "high":
        action = "VENTILATION_ON"
        reason = f"Risk transitioned {prev or 'low'} → high; forcing simulated fresh air exchange."
    elif risk_now == "high" and streak >= 2 and temp_now >= 24.5:
        action = "HVAC_COOL_ON"
        reason = f"High risk streak × {streak} reads (T={temp_now:.1f}°C); starting supplementary cooling."
    elif prev == "high" and risk_now != "high":
        action = "VENTILATION_OFF"
        reason = f"Risk level normalized to {risk_now}; cancelling simulated forced ventilation."

    if action:
        try:
            db.insert_actuation(conn, now_ts, action, room, reason)
        except Exception:
            pass

    st.session_state["_last_risk"] = risk_now


# ---------------------------------------------------------------------------
# Sidebar Controls & Privacy Architecture Explainer
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>
            <span style='font-size:1.6rem;'>🛡️</span>
            <div>
                <b style='font-size:1.15rem;color:#ffffff;letter-spacing:-0.01em;'>Aegis</b>
                <div style='font-size:0.75rem;color:#00e5ff;text-transform:uppercase;'>Room Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Privacy-preserving environmental intelligence for edge IoT.")
    st.markdown("---")

    # Room Selector
    conn_preview = _ensure_conn()
    available_rooms = [ROOM_DEFAULT]
    if conn_preview is not None:
        try:
            r_df = pd.read_sql_query("SELECT DISTINCT room_id FROM telemetry LIMIT 10;", conn_preview)
            if not r_df.empty:
                available_rooms = sorted(list(set(r_df["room_id"].dropna().tolist())))
        except Exception:
            pass
    if ROOM_DEFAULT not in available_rooms:
        available_rooms.insert(0, ROOM_DEFAULT)

    selected_room = st.selectbox(
        "Monitored Space",
        options=available_rooms,
        index=0,
        help="Select room telemetry stream to inspect.",
    )

    # Time Window Selector
    window_choice = st.radio(
        "Time Range Window",
        options=["15m", "1h", "6h", "24h"],
        index=1,
        horizontal=True,
        help="Rolling aggregation window for charts and analysis.",
    )
    window_map = {"15m": 15, "1h": 60, "6h": 360, "24h": 1440}
    window_minutes = window_map[window_choice]

    st.markdown("---")

    # Non-technical Privacy & Security Architecture Explainer
    with st.expander("🛡️ Privacy & Security", expanded=True):
        st.markdown(
            """
            **Privacy-by-Design Architecture**  
            Aegis only visualizes 1-minute statistical aggregations. Raw high-frequency sensor samples never leave the simulator sandbox, guaranteeing zero exposure of sub-second readings. All telemetry in transit is strictly encrypted via TLS over MQTT (port 8883), with zero cameras, microphones, or biometric tracking.
            """
        )

    st.markdown("---")

    # Refresh & System Controls
    col_ref, col_info = st.columns([1, 1])
    with col_ref:
        if st.button("⟳ Refresh", use_container_width=True):
            st.rerun()
    with col_info:
        st.caption(f"Sync: `{REFRESH_SEC}s`")

    st.caption(f"SQLite Store: `{DB_PATH}`")


# ---------------------------------------------------------------------------
# Core Dashboard View Orchestration
# ---------------------------------------------------------------------------
def _render_dashboard_content(room: str, win_min: int):
    """Render the full HUD, KPIs, charts, risk panel, and actuation feed."""
    conn = _ensure_conn()

    # Pull telemetry & predictions
    tele_df = pd.DataFrame()
    pred_df = pd.DataFrame()
    act_df = pd.DataFrame()
    latest_ts: Optional[int] = None

    if conn is not None:
        tele_df = db.query_recent_telemetry(conn, minutes=win_min)
        pred_df = db.query_recent_predictions(conn, minutes=win_min * 2)
        act_df = db.query_latest_actuation(conn, limit=100)

    # Calculate Staleness
    now_epoch_ms = int(time.time() * 1000)
    is_stale = False
    stale_minutes = 0.0

    if not tele_df.empty:
        latest_ts = int(tele_df["ts"].iloc[-1])
        stale_seconds = max(0.0, (now_epoch_ms - latest_ts) / 1000.0)
        stale_minutes = stale_seconds / 60.0
        # Pipeline is stale if > 5 minutes old (or > 3x the 1-minute publish rate)
        if stale_minutes > 5.0:
            is_stale = True

    # 1. Top Bar HUD
    st.markdown(
        render_top_bar(
            room_name=room,
            latest_ts=latest_ts,
            is_stale=is_stale,
            stale_minutes=stale_minutes,
        ),
        unsafe_allow_html=True,
    )

    # 2. Stale Warning Banner (if stale)
    if is_stale and latest_ts is not None:
        st.markdown(
            f"""
            <div class='stale-warning-banner'>
                <span style='font-size:1.2rem;'>⚠️</span>
                <div>
                    <b>Pipeline Warning:</b> No new sensor data in <b>{stale_minutes:.1f} minutes</b>
                    (expected interval: 1 min). Verify that the simulator publisher and MQTT broker are healthy.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 3. Graceful Empty State (if no telemetry at all)
    if tele_df.empty:
        st.markdown(
            """
            <div class='empty-state-card'>
                <div class='empty-state-icon'>📡</div>
                <div class='empty-state-title'>Waiting for the first reading...</div>
                <div class='empty-state-desc'>
                    No telemetry records found for this room. Ensure the AIoT simulator is running and publishing 
                    aggregated 1-minute packets to <code>home/room1/telemetry</code>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Extract latest readings & calculate window deltas
    last_t = float(tele_df["temperature"].iloc[-1])
    last_h = float(tele_df["humidity"].iloc[-1])
    last_c = float(tele_df["co2"].iloc[-1])
    last_m = int(tele_df["motion"].iloc[-1])

    delta_t: Optional[float] = None
    delta_h: Optional[float] = None
    delta_c: Optional[float] = None
    delta_m: str = "Stable"

    if len(tele_df) >= 2:
        prev_t = float(tele_df["temperature"].iloc[-2])
        prev_h = float(tele_df["humidity"].iloc[-2])
        prev_c = float(tele_df["co2"].iloc[-2])
        prev_m = int(tele_df["motion"].iloc[-2])

        delta_t = last_t - prev_t
        delta_h = last_h - prev_h
        delta_c = last_c - prev_c

        if last_m == 1 and prev_m == 0:
            delta_m = "▲ Motion Started"
        elif last_m == 0 and prev_m == 1:
            delta_m = "▼ Motion Cleared"
        elif last_m == 1:
            delta_m = "● Sustained Motion"
        else:
            delta_m = "○ Continuous Idle"
    else:
        delta_m = "First Window"

    # ML Risk Inference & Actuation
    prev_risk = str(pred_df["risk_level"].iloc[-1]) if not pred_df.empty else None
    risk_now, risk_conf, risk_probs = _predict_risk_and_infer(conn, latest_ts, win_min)
    _simulate_actuation(conn, risk_now, prev_risk, room)

    # 4. Row of KPI Cards with Badges
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="Temperature",
            value=f"{last_t:.1f} °C",
            delta=f"{delta_t:+.2f} °C" if delta_t is not None else None,
        )
        st.markdown(kpi_status_badge("temperature", last_t), unsafe_allow_html=True)

    with k2:
        st.metric(
            label="Humidity",
            value=f"{last_h:.1f} %",
            delta=f"{delta_h:+.1f} %" if delta_h is not None else None,
        )
        st.markdown(kpi_status_badge("humidity", last_h), unsafe_allow_html=True)

    with k3:
        st.metric(
            label="CO₂ Concentration",
            value=f"{int(round(last_c))} ppm",
            delta=f"{int(round(delta_c)):+d} ppm" if delta_c is not None else None,
            delta_color="inverse",
        )
        st.markdown(kpi_status_badge("co2", last_c), unsafe_allow_html=True)

    with k4:
        st.metric(
            label="Motion (PIR Latch)",
            value="Active" if last_m == 1 else "Clear",
            delta=delta_m,
        )
        st.markdown(kpi_status_badge("motion", float(last_m)), unsafe_allow_html=True)

    # 5. Main Chart: Rolling Time-Series
    st.markdown(
        f"""
        <div class='section-header'>
            <div class='section-title'>📊 Environmental Telemetry Dynamics</div>
            <div class='section-subtitle'>Rolling {win_min}-minute window · Temperature, Humidity, and CO₂</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        time_series_chart(tele_df, pred_df, window_minutes=win_min),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # 6. Occupancy / Motion Timeline Directly Beneath Main Chart
    st.markdown(
        """
        <div class='section-header' style='margin-top: 0.2rem;'>
            <div class='section-title'>🚶 Occupancy & Motion Timeline</div>
            <div class='section-subtitle'>Correlated against CO₂ and temperature fluctuations above</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        motion_timeline_chart(tele_df, window_minutes=win_min),
        use_container_width=True,
        config={"displayModeBar": False},
    )

    # 7. Lower Section: Risk Intelligence Panel & Actuation Activity Feed
    lower_left, lower_right = st.columns([1, 1], gap="medium")

    with lower_left:
        st.markdown(
            """
            <div class='section-header'>
                <div class='section-title'>🧠 ML Risk Classification</div>
                <div class='section-subtitle'>RandomForest model live inference</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            risk_badge(
                risk_level=risk_now,
                confidence=risk_conf,
                model_version=MODEL_VERSION,
                probabilities=risk_probs,
            ),
            unsafe_allow_html=True,
        )
        st.markdown("<div style='font-size:0.75rem;color:#64748b;margin-bottom:4px;'>RECENT RISK TRANSITIONS</div>", unsafe_allow_html=True)
        st.plotly_chart(
            risk_history_sparkline(pred_df, last_n=45),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with lower_right:
        st.markdown(
            """
            <div class='section-header'>
                <div class='section-title'>📋 Simulated Actuation Feed</div>
                <div class='section-subtitle'>Automated actions triggered by risk policy</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(render_actuation_feed(act_df, limit=40), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Auto-Refresh Strategy (Flicker-Free Native Fragments)
# ---------------------------------------------------------------------------
# Modern Streamlit (1.34+) supports @st.fragment or @st.experimental_fragment
# which reruns ONLY the decorated block every N seconds without full page flicker.
_fragment_decorator = getattr(st, "fragment", getattr(st, "experimental_fragment", None))

if _fragment_decorator is not None:
    @_fragment_decorator(run_every=REFRESH_SEC)
    def live_dashboard_fragment(room: str, win_min: int):
        _render_dashboard_content(room, win_min)

    live_dashboard_fragment(selected_room, window_minutes)
else:
    # Fallback to streamlit-autorefresh if available, otherwise placeholder sleep
    try:
        from streamlit_autorefresh import st_autorefresh  # type: ignore

        st_autorefresh(interval=REFRESH_SEC * 1000, key="aegis_refresh", debounce=True)
        _render_dashboard_content(selected_room, window_minutes)
    except Exception:
        # Graceful placeholder loop fallback
        dashboard_slot = st.empty()
        with dashboard_slot.container():
            _render_dashboard_content(selected_room, window_minutes)
        time.sleep(REFRESH_SEC)
        st.rerun()
