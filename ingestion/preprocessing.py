"""Cleaning, resampling, and feature engineering for the AIoT telemetry stream.

Pipeline (applied in :func:`run_pipeline`):
    1. Pull raw ``telemetry`` rows from SQLite.
    2. IQR-based outlier CLAMPING on numeric columns (preserves timestamps and
       avoids dropping rows — important for small datasets).
    3. Resample to a fixed 1-minute cadence using pandas ``asfreq`` with
       linear interpolation for small gaps (<=5 min). Gaps longer than that
       remain NaN and are later forward-filled for features only.
    4. Engineer rolling + rate-of-change + time-of-day features.

The resulting wide ``features`` table is the sole input to the ML training
and live dashboard inference code.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd

# Allow running as __main__ or imported module.
if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ingestion import database as db
else:
    from . import database as db


log = logging.getLogger("preprocessing")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [preprocessing] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


NUMERIC_COLS: Sequence[str] = ("temperature", "humidity", "co2", "motion")
# Physically-plausible caps applied before IQR clipping. Keeps any rogue
# values (e.g. CO2=1e9 from a corrupted MQTT message) from blowing up stats.
HARD_CLIP: dict = {
    "temperature": (-40.0, 80.0),
    "humidity": (0.0, 100.0),
    "co2": (0.0, 10_000.0),
    "motion": (0, 1),
}


# ---------------------------------------------------------------------------
# Outlier removal.
# ---------------------------------------------------------------------------
def remove_outliers_iqr(
    df: pd.DataFrame,
    cols: Optional[Sequence[str]] = None,
    k: float = 1.5,
) -> pd.DataFrame:
    """IQR-based CLAMPING (not dropping) per column.

    Dropping rows on 1-minute telemetry can introduce gaps that confuse
    rolling-window features. Clamping to ``[Q1 - k*IQR, Q3 + k*IQR]``
    keeps the time axis regular while taming spikes.
    """
    df = df.copy()
    cols = list(cols or [c for c in NUMERIC_COLS if c in df.columns])
    for c in cols:
        if c in HARD_CLIP:
            lo, hi = HARD_CLIP[c]
            df[c] = df[c].clip(lower=lo, upper=hi)
        if df[c].dtype.kind not in ("i", "u", "f"):
            continue
        q1 = df[c].quantile(0.25)
        q3 = df[c].quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        df[c] = df[c].clip(lower=q1 - k * iqr, upper=q3 + k * iqr)
    return df


# ---------------------------------------------------------------------------
# Resampling.
# ---------------------------------------------------------------------------
def _to_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(datetime=pd.Series(dtype="datetime64[ns, UTC]")).set_index(
            "datetime"
        )
    out = df.copy()
    out["datetime"] = pd.to_datetime(out["ts"], unit="ms", utc=True)
    return out.set_index("datetime").sort_index()


def resample_fixed(
    df: pd.DataFrame,
    rule: str = "1min",
    method: str = "mean",
    interpolate_gaps_max_min: int = 5,
) -> pd.DataFrame:
    """Resample irregular telemetry onto a fixed ``rule`` cadence.

    Small gaps (≤ ``interpolate_gaps_max_min`` minutes) are linearly
    interpolated; larger gaps remain NaN and are forward-filled during
    the feature-engineering step only for rolling inputs.
    """
    if df.empty:
        return df
    d = _to_datetime_index(df)
    numeric_cols = [c for c in NUMERIC_COLS if c in d.columns]
    other_cols = [c for c in d.columns if c not in numeric_cols and c != "ts"]

    agg: dict = {c: method for c in numeric_cols}
    # Preserve room_id / metadata by taking the first non-null per bucket.
    for c in other_cols:
        agg[c] = "first"
    if "room_id" in d.columns and "room_id" not in agg:
        agg["room_id"] = "first"

    resampled = d.resample(rule).agg(agg)
    # Linear interpolation for small gaps.
    limit = max(1, int(interpolate_gaps_max_min))
    for c in numeric_cols:
        if c in resampled.columns:
            resampled[c] = resampled[c].interpolate(
                method="time", limit=limit, limit_direction="both"
            )
    # Preserve ts (index -> ms epoch) alongside the datetime index for convenience.
    resampled["ts"] = (resampled.index.astype("int64") // 1_000_000).astype("int64")
    resampled.reset_index(drop=False, inplace=True)
    return resampled


# ---------------------------------------------------------------------------
# Feature engineering.
# ---------------------------------------------------------------------------
def _roll(df: pd.DataFrame, col: str, wins: Sequence[int]) -> pd.DataFrame:
    out = df.copy()
    for w in wins:
        prefix = col.replace("temperature", "temp").replace("humidity", "hum")
        r = out[col].rolling(window=w, min_periods=max(2, w // 3))
        out[f"{prefix}_mean_{w}"] = r.mean()
        out[f"{prefix}_std_{w}"] = r.std(ddof=0).fillna(0.0)
    return out


def _rate(df: pd.DataFrame, col: str, dt_minutes: float = 1.0) -> pd.Series:
    """First-difference rate per minute."""
    return df[col].diff() / dt_minutes


def engineer_features(df: pd.DataFrame, wins: Sequence[int] = (5, 15)) -> pd.DataFrame:
    """Append rolling + rate + time-of-day features.

    Produces at minimum the columns required by
    ``ml/train.py`` / live inference in ``dashboard/app.py``:
      - temp_mean_5, temp_std_5, temp_mean_15, temp_std_15
      - hum_mean_5,  hum_std_5,  hum_mean_15,  hum_std_15
      - co2_mean_5,  co2_std_5,  co2_mean_15,  co2_std_15
      - temp_rate, hum_rate, co2_rate
      - hour, is_daytime
    """
    df = df.copy()
    if df.empty:
        for c in [
            "temp_mean_5", "temp_std_5", "temp_mean_15", "temp_std_15",
            "hum_mean_5", "hum_std_5", "hum_mean_15", "hum_std_15",
            "co2_mean_5", "co2_std_5", "co2_mean_15", "co2_std_15",
            "temp_rate", "hum_rate", "co2_rate", "hour", "is_daytime",
        ]:
            df[c] = pd.Series(dtype="float64")
        return df

    # Forward-fill small NaN patches leftover from resample gaps so rolling
    # windows don't cascade NaNs. This is feature-only — telemetry table is
    # never mutated.
    for c in ("temperature", "humidity", "co2", "motion"):
        df[c] = df[c].ffill().bfill()

    for col in ("temperature", "humidity", "co2"):
        df = _roll(df, col, wins)
    df["temp_rate"] = _rate(df, "temperature")
    df["hum_rate"] = _rate(df, "humidity")
    df["co2_rate"] = _rate(df, "co2")

    if "datetime" not in df.columns:
        df["datetime"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df["hour"] = df["datetime"].dt.hour.astype("int32")
    df["is_daytime"] = ((df["hour"] >= 6) & (df["hour"] < 18)).astype("int32")

    rate_cols = ["temp_rate", "hum_rate", "co2_rate"]
    df[rate_cols] = df[rate_cols].fillna(0.0)
    return df


# ---------------------------------------------------------------------------
# End-to-end pipeline.
# ---------------------------------------------------------------------------
def run_pipeline(
    db_path: Optional[str] = None,
    out_table: str = "features",
) -> pd.DataFrame:
    """Run the full pipeline: telemetry → cleaning → resample → features → DB.

    Returns
    -------
    pd.DataFrame
        The final features table written to SQLite.
    """
    db_path = db_path or os.environ.get("DB_PATH", "./data/iot.db")
    conn = db.init_db(db_path)
    raw = db.query_all_telemetry(conn)
    log.info(f"Loaded {len(raw)} raw telemetry rows")

    if raw.empty:
        log.warning("No telemetry rows yet — nothing to preprocess.")
        return pd.DataFrame()

    cleaned = remove_outliers_iqr(raw)
    resampled = resample_fixed(cleaned)
    features = engineer_features(resampled)

    cols_order = [
        "ts", "temperature", "humidity", "co2", "motion",
        "temp_mean_5", "temp_std_5", "temp_mean_15", "temp_std_15",
        "hum_mean_5", "hum_std_5", "hum_mean_15", "hum_std_15",
        "co2_mean_5", "co2_std_5", "co2_mean_15", "co2_std_15",
        "temp_rate", "hum_rate", "co2_rate",
        "hour", "is_daytime",
    ]
    cols_order = [c for c in cols_order if c in features.columns]
    features_out = features[cols_order].copy()

    if out_table == "features":
        n = db.replace_features(conn, features_out)
        log.info(f"Wrote {n} feature rows -> SQLite features table")
    return features_out.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Smoke test with synthetic data.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Build a tiny synthetic 100-row "1-minute telemetry" with a fake occupancy
    # spike so all features produce non-trivial values.
    rng = np.random.default_rng(42)
    n = 120
    t0 = int(pd.Timestamp("2024-01-01 08:00:00", tz="UTC").timestamp() * 1000)
    rows = []
    temp, hum, co2 = 21.5, 45.0, 450.0
    for i in range(n):
        temp += rng.normal(0, 0.1)
        hum += rng.normal(0, 0.4)
        if 30 <= i <= 60:
            co2 = min(co2 + rng.normal(15, 4), 1400)
            motion = 1 if rng.random() < 0.85 else 0
        else:
            co2 = max(co2 + rng.normal(-6, 3), 420)
            motion = 1 if rng.random() < 0.04 else 0
        rows.append(
            {
                "ts": t0 + i * 60_000,
                "temperature": round(temp, 2),
                "humidity": round(float(np.clip(hum, 10, 90)), 2),
                "co2": float(round(co2)),
                "motion": motion,
                "room_id": "room1",
            }
        )
    df_raw = pd.DataFrame(rows)
    cleaned = remove_outliers_iqr(df_raw)
    rs = resample_fixed(cleaned)
    feats = engineer_features(rs)

    print("Feature columns produced:")
    print("  " + "\n  ".join(feats.columns.tolist()))
    print()
    print("Tail of features (last 5 rows):")
    show_cols = [
        "ts", "temperature", "co2", "motion",
        "temp_mean_5", "co2_std_5", "temp_rate", "hour", "is_daytime",
    ]
    show_cols = [c for c in show_cols if c in feats.columns]
    with pd.option_context("display.width", 160, "display.max_columns", 20):
        print(feats[show_cols].tail().to_string(index=False))
