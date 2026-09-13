"""Streamlit live dashboard for the AIoT privacy-aware stack.

Layout
------
Row 1   : 4 gauges (temp, humidity, CO2, motion).
Row 2   : Dual-axis rolling time-series (last ~60 min).
Row 3   : Current risk badge + short explanation (left)  | risk sparkline (right).
Row 4   : Simulated actuation log panel.

Auto-refreshes every ``REFRESH_SEC`` seconds (default 10).

On each refresh, if the latest feature row + saved RandomForest model are
available, we predict a risk class and store it in the ``predictions`` table.
If the risk crosses to ``high`` (or stays ``high`` for 2+ consecutive reads),
we log a SIMULATED actuation action — nothing physical is ever actuated.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

import dotenv
import joblib
import pandas as pd
import streamlit as st

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ingestion import database as db
    from ingestion import preprocessing
    from dashboard.components import gauge, risk_badge, risk_history_sparkline, time_series_chart
    from ml.train import FEATURE_COLUMNS, _select_X
else:
    from ingestion import database as db
    from ingestion import preprocessing
    from .components import gauge, risk_badge, risk_history_sparkline, time_series_chart
    from ml.train import FEATURE_COLUMNS, _select_X


dotenv.load_dotenv()

REFRESH_SEC = int(os.environ.get("REFRESH_SEC", "10"))
DB_PATH = os.environ.get("DB_PATH", "./data/iot.db")
WINDOW_MIN = int(os.environ.get("DASH_WINDOW_MIN", "60"))
ROOM = os.environ.get("ROOM_ID", "room1")
MODEL_DIR = Path(__file__).resolve().parent.parent / "ml" / "models"
MODEL_VERSION = "random_forest_v1"
MODEL_PATH = MODEL_DIR / f"{MODEL_VERSION}.joblib"


# ---------------------------------------------------------------------------
# Streamlit bootstrap.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AIoT Privacy Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("🌿 AIoT Privacy Dashboard")
    st.caption(
        "Privacy-by-design demo. Only 1-min aggregated sensor readings are "
        "published — raw per-second samples never leave the simulator."
    )
    st.markdown("---")
    st.metric("Room", ROOM)
    st.metric("Refresh", f"{REFRESH_SEC} s")
    st.metric("Time window", f"{WINDOW_MIN} min")
    st.markdown("---")
    if st.button("⟳ Refresh now"):
        st.rerun()
    st.caption(f"SQLite DB: `{DB_PATH}`")


def _ensure_conn():
    try:
        return db.init_db(DB_PATH)
    except Exception as exc:
        st.error(f"Failed to open SQLite DB at {DB_PATH}: {exc}")
        return None


def _load_latest_model():
    if not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _predict_if_possible(conn, latest_ts: Optional[int]) -> Optional[str]:
    """Load latest feature row, run RF prediction, persist + return risk."""
    if conn is None:
        return None
    model = _load_latest_model()
    if model is None:
        return None
    features = db.query_all_features(conn)
    if features.empty:
        return None
    # Build feature input exactly as ml/train.py does.
    X_all = _select_X(features)
    if X_all.empty:
        return None
    last_row_df = X_all.iloc[[-1]].copy()
    ts_row = int(features["ts"].iloc[-1])
    # Don't re-predict the same ts twice.
    preds = db.query_recent_predictions(conn, minutes=WINDOW_MIN * 2)
    if not preds.empty and int(preds["ts"].iloc[-1]) >= ts_row:
        return str(preds["risk_level"].iloc[-1])
    pred = str(model.predict(last_row_df)[0])
    try:
        db.insert_prediction(conn, ts_row, pred, MODEL_VERSION)
    except Exception:
        pass
    if latest_ts is not None and ts_row != latest_ts:
        return pred
    return pred


def _simulate_actuation(conn, risk_now: str, prev_risk: Optional[str]) -> None:
    """SIMULATED actuation: log only. No physical devices are controlled.

    Rules (arbitrary but realistic):
      - risk transitions low/medium → high → VENTILATION_ON
      - stays high 2+ consecutive reads         → HVAC_COOL_ON if temp is high
      - transitions high → low/medium            → VENTILATION_OFF
    """
    if conn is None or risk_now is None:
        return
    now_ts = int(time.time() * 1000)

    # Persist counters in Streamlit session_state between refreshes.
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
        reason = f"Risk transitioned {prev or 'low'} → high; forcing fresh air."
    elif risk_now == "high" and streak >= 2 and temp_now >= 24.5:
        action = "HVAC_COOL_ON"
        reason = f"High risk × {streak} reads (T={temp_now:.1f}°C); starting cooling."
    elif prev == "high" and risk_now != "high":
        action = "VENTILATION_OFF"
        reason = f"Risk back to {risk_now}; cancelling forced ventilation."

    if action:
        try:
            db.insert_actuation(conn, now_ts, action, ROOM, reason)
        except Exception:
            pass

    st.session_state["_last_risk"] = risk_now


# ---------------------------------------------------------------------------
# Main UI.
# ---------------------------------------------------------------------------
st.title("🌿 Privacy-Aware Smart IoT Dashboard")
st.caption(
    "Live view of privacy-aggregated telemetry + ML risk classification. "
    "No raw per-second sensor samples, cameras, audio, or identity data are "
    "collected anywhere in the pipeline."
)

conn = _ensure_conn()

# Auto-refresh: use st_autorefresh-like pattern via time.sleep + rerun after
# rendering. The community component st_autorefresh avoids the sleep in a
# callback but isn't always installed; we fall back to a simple meta-refresh
# through st.empty and Streamlit's native rerun() mechanism.
try:
    from streamlit_autorefresh import st_autorefresh  # type: ignore

    st_autorefresh(interval=REFRESH_SEC * 1000, key="dashref", debounce=True)
except Exception:
    # No autorefresh package — emulate with a placeholder and sleep.
    refresh_placeholder = st.empty()
    # We still rerun at the bottom via time.sleep + st.rerun.

# Pull data.
tele_df = pd.DataFrame()
pred_df = pd.DataFrame()
act_df = pd.DataFrame()
latest_ts: Optional[int] = None
if conn is not None:
    tele_df = db.query_recent_telemetry(conn, minutes=WINDOW_MIN)
    pred_df = db.query_recent_predictions(conn, minutes=WINDOW_MIN * 2)
    act_df = db.query_latest_actuation(conn, limit=200)

# Latest numeric values.
last_t = tele_df["temperature"].iloc[-1] if not tele_df.empty else float("nan")
last_h = tele_df["humidity"].iloc[-1] if not tele_df.empty else float("nan")
last_c = tele_df["co2"].iloc[-1] if not tele_df.empty else float("nan")
last_m = int(tele_df["motion"].iloc[-1]) if not tele_df.empty else 0
if not tele_df.empty:
    latest_ts = int(tele_df["ts"].iloc[-1])

prev_risk = None
if not pred_df.empty:
    prev_risk = str(pred_df["risk_level"].iloc[-1])

# Predict current risk.
risk_now = _predict_if_possible(conn, latest_ts)
_simulate_actuation(conn, risk_now, prev_risk)
if risk_now is None and prev_risk is not None:
    risk_now = prev_risk

# --- Row 1: four gauges.
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.plotly_chart(
        gauge(last_t if pd.notna(last_t) else 0.0, 10, 35, "Temperature", "°C",
              warning_threshold=25.0, danger_threshold=26.5),
        use_container_width=True,
    )
with c2:
    st.plotly_chart(
        gauge(last_h if pd.notna(last_h) else 0.0, 10, 90, "Humidity", "%",
              warning_threshold=65.0, danger_threshold=70.0),
        use_container_width=True,
    )
with c3:
    st.plotly_chart(
        gauge(last_c if pd.notna(last_c) else 0.0, 350, 2000, "CO₂", "ppm",
              warning_threshold=800.0, danger_threshold=1000.0),
        use_container_width=True,
    )
with c4:
    fig_mot = gauge(
        float(last_m), 0.0, 1.0, "Motion (PIR)", "latch/max",
        danger_threshold=0.5,
    )
    st.plotly_chart(fig_mot, use_container_width=True)

# --- Row 2: time-series.
st.plotly_chart(
    time_series_chart(tele_df, pred_df, window_minutes=WINDOW_MIN),
    use_container_width=True,
)

# --- Row 3: risk badge + sparkline.
rleft, rright = st.columns([1, 1])
with rleft:
    st.subheader("Current air-quality / occupancy risk")
    rl = risk_now or "low"
    st.markdown(risk_badge(rl), unsafe_allow_html=True)
    st.markdown("")
    explanations = {
        "low":    "Room appears unoccupied and well-ventilated. No action needed.",
        "medium": "Room occupied; CO₂ climbing but still within acceptable bounds.",
        "high":   "Poor air quality detected — forcing simulated ventilation.",
    }
    st.info(explanations.get(rl, explanations["low"]))
    st.caption(
        f"Model version: `{MODEL_VERSION}`  |  Backend: SQLite + RandomForest  |  "
        f"MQTT broker: TLS on 8883"
    )
with rright:
    st.subheader("Risk history (last reads)")
    st.plotly_chart(risk_history_sparkline(pred_df, last_n=60), use_container_width=True)

# --- Row 4: actuation log.
st.subheader("📋 Simulated actuation log")
st.caption(
    "All actions are simulated for UI demonstration. No physical HVAC, vents, "
    "lights, or relays exist anywhere in this software-only simulator stack."
)
if act_df.empty:
    st.info("No actuation events yet — wait until the ML class predicts HIGH risk.")
else:
    act_show = act_df.copy()
    act_show["when"] = pd.to_datetime(act_show["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    act_show = act_show[["when", "action", "room", "reason"]].tail(50)
    st.dataframe(act_show, use_container_width=True, hide_index=True)

# Fallback auto-refresh without st_autorefresh package.
if "st_autorefresh" not in sys.modules:
    refresh_placeholder.caption(f"Auto-refresh every {REFRESH_SEC}s …")
    time.sleep(REFRESH_SEC)
    st.rerun()
