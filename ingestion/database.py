"""SQLite schema + helpers for the AIoT ingestion / dashboard persistence layer.

A single SQLite file lives on a shared volume mounted by both the ingestion
service (writes) and the dashboard (reads). WAL mode is enabled so the
dashboard's reader transactions don't block ingestion writer transactions.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Thread-safe single connection pool (one per process, one per DB path).
# ---------------------------------------------------------------------------
_LOCK = threading.Lock()
_CONNS: Dict[str, sqlite3.Connection] = {}


def _ensure_parent_dir(db_path: str) -> None:
    parent = Path(db_path).resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def get_conn(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a cached SQLite connection with sensible PRAGMAs set.

    Callers should *not* close the returned connection — it is reused for
    the lifetime of the process and only closed on :func:`close_all`.
    """
    is_mem = False
    if db_path is None:
        db_path = os.environ.get("DB_PATH", "./data/iot.db")
    if str(db_path).strip() == ":memory:":
        is_mem = True
        db_path_key = ":memory:"
    else:
        db_path_key = str(Path(db_path).resolve())
    with _LOCK:
        conn = _CONNS.get(db_path_key)
        if conn is None:
            if not is_mem:
                _ensure_parent_dir(db_path_key)
            conn = sqlite3.connect(
                ":memory:" if is_mem else db_path_key,
                check_same_thread=False,
                timeout=30.0,
            )
            conn.row_factory = sqlite3.Row
            # Concurrent read/write safety for dashboard + ingestion.
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            _CONNS[db_path] = conn
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Lightweight commit/rollback context manager."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def close_all() -> None:
    with _LOCK:
        for c in _CONNS.values():
            try:
                c.close()
            except Exception:
                pass
        _CONNS.clear()


# ---------------------------------------------------------------------------
# Schema.
# ---------------------------------------------------------------------------
_SCHEMA_STATEMENTS: List[str] = [
    """
    CREATE TABLE IF NOT EXISTS telemetry (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ts          INTEGER NOT NULL,             -- epoch ms (window end)
        temperature REAL,                         -- °C, mean over 1 min
        humidity    REAL,                         -- % , mean over 1 min
        co2         REAL,                         -- ppm, mean over 1 min
        motion      INTEGER NOT NULL DEFAULT 0,   -- 0/1, max (latching PIR)
        room_id     TEXT NOT NULL DEFAULT 'room1'
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(ts);",
    "CREATE INDEX IF NOT EXISTS idx_telemetry_room_ts ON telemetry(room_id, ts);",
    """
    CREATE TABLE IF NOT EXISTS predictions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        ts             INTEGER NOT NULL,
        risk_level     TEXT NOT NULL,            -- 'low' | 'medium' | 'high'
        model_version  TEXT NOT NULL             -- e.g. 'random_forest_v1'
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_predictions_ts ON predictions(ts);",
    """
    CREATE TABLE IF NOT EXISTS features (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER NOT NULL UNIQUE,
        temperature REAL,
        humidity REAL,
        co2 REAL,
        motion REAL,
        temp_mean_5 REAL, temp_std_5 REAL,
        temp_mean_15 REAL, temp_std_15 REAL,
        hum_mean_5 REAL, hum_std_5 REAL,
        hum_mean_15 REAL, hum_std_15 REAL,
        co2_mean_5 REAL, co2_std_5 REAL,
        co2_mean_15 REAL, co2_std_15 REAL,
        temp_rate REAL, hum_rate REAL, co2_rate REAL,
        hour INTEGER,
        is_daytime INTEGER
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_features_ts ON features(ts);",
    """
    CREATE TABLE IF NOT EXISTS actuation_log (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        ts     INTEGER NOT NULL,
        action TEXT NOT NULL,
        room   TEXT NOT NULL,
        reason TEXT NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_actuation_ts ON actuation_log(ts);",
]


def init_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Idempotently create every table/index. Safe to call at boot."""
    conn = get_conn(db_path)
    with transaction(conn):
        for stmt in _SCHEMA_STATEMENTS:
            conn.execute(stmt)
    return conn


# ---------------------------------------------------------------------------
# Insert helpers.
# ---------------------------------------------------------------------------
_TELEMETRY_COLS = ("ts", "temperature", "humidity", "co2", "motion", "room_id")


def insert_telemetry(conn: sqlite3.Connection, row: Dict[str, Any]) -> int:
    """Insert one telemetry row from a MQTT payload dict. Returns lastrowid."""
    cols = [c for c in _TELEMETRY_COLS if c in row]
    placeholders = ", ".join(["?"] * len(cols))
    values = [row[c] for c in cols]
    sql = f"INSERT INTO telemetry ({', '.join(cols)}) VALUES ({placeholders});"
    with transaction(conn):
        cur = conn.execute(sql, values)
    return int(cur.lastrowid)


def insert_telemetry_many(conn: sqlite3.Connection, rows: Iterable[Dict[str, Any]]) -> int:
    """Bulk insert; returns number of rows inserted."""
    rows = list(rows)
    if not rows:
        return 0
    cols = [c for c in _TELEMETRY_COLS if c in rows[0]]
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO telemetry ({', '.join(cols)}) VALUES ({placeholders});"
    values = [[r.get(c) for c in cols] for r in rows]
    with transaction(conn):
        conn.executemany(sql, values)
    return len(values)


def insert_prediction(
    conn: sqlite3.Connection, ts: int, risk_level: str, model_version: str
) -> int:
    sql = (
        "INSERT INTO predictions (ts, risk_level, model_version) VALUES (?, ?, ?);"
    )
    with transaction(conn):
        cur = conn.execute(sql, (int(ts), str(risk_level), str(model_version)))
    return int(cur.lastrowid)


def insert_actuation(
    conn: sqlite3.Connection,
    ts: int,
    action: str,
    room: str,
    reason: str = "",
) -> int:
    sql = "INSERT INTO actuation_log (ts, action, room, reason) VALUES (?, ?, ?, ?);"
    with transaction(conn):
        cur = conn.execute(sql, (int(ts), str(action), str(room), str(reason)))
    return int(cur.lastrowid)


def replace_features(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    """Full rewrite of the ``features`` table from a DataFrame.

    This is fine for a single-room simulation; the table size stays small
    (~1440 rows/day).

    Defensive against duplicate ``ts`` values within a single batch (which
    can occur if the preprocessing pipeline produces overlapping windows):
    duplicates are collapsed, keeping the last occurrence, and the insert
    uses INSERT OR REPLACE so a stray duplicate ts can never raise a
    UNIQUE constraint error even if dedup logic elsewhere is imperfect.
    """
    if df.empty:
        return 0

    cols = [c for c in df.columns if c.lower() not in ("id",)]
    df = df[cols].copy()

    # Defend against duplicate ts within this batch (root cause of the
    # UNIQUE constraint failures) — keep the most recent computed row.
    if "ts" in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=["ts"], keep="last")
        dropped = before - len(df)
        if dropped:
            print(f"[database] WARNING: dropped {dropped} duplicate ts row(s) before writing features")

    with transaction(conn):
        conn.execute("DELETE FROM features;")

    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT OR REPLACE INTO features ({', '.join(cols)}) VALUES ({placeholders});"
    values = [tuple(r) for r in df.itertuples(index=False, name=None)]
    with transaction(conn):
        conn.executemany(sql, values)
    return len(values)


# ---------------------------------------------------------------------------
# Query helpers.
# ---------------------------------------------------------------------------
def _query_df(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params)


def query_recent_telemetry(
    conn: sqlite3.Connection, minutes: int = 60
) -> pd.DataFrame:
    cutoff = int((pd.Timestamp.utcnow().timestamp() - minutes * 60) * 1000)
    sql = (
        "SELECT ts, temperature, humidity, co2, motion, room_id FROM telemetry "
        "WHERE ts >= ? ORDER BY ts ASC;"
    )
    return _query_df(conn, sql, (cutoff,))


def query_recent_predictions(
    conn: sqlite3.Connection, minutes: int = 60
) -> pd.DataFrame:
    cutoff = int((pd.Timestamp.utcnow().timestamp() - minutes * 60) * 1000)
    sql = (
        "SELECT ts, risk_level, model_version FROM predictions "
        "WHERE ts >= ? ORDER BY ts ASC;"
    )
    return _query_df(conn, sql, (cutoff,))


def query_all_telemetry(conn: sqlite3.Connection) -> pd.DataFrame:
    return _query_df(
        conn,
        "SELECT ts, temperature, humidity, co2, motion, room_id FROM telemetry ORDER BY ts ASC;",
    )


def query_all_features(conn: sqlite3.Connection) -> pd.DataFrame:
    return _query_df(conn, "SELECT * FROM features ORDER BY ts ASC;")


def query_latest_actuation(conn: sqlite3.Connection, limit: int = 100) -> pd.DataFrame:
    sql = (
        "SELECT ts, action, room, reason FROM actuation_log "
        "ORDER BY ts DESC LIMIT ?;"
    )
    df = _query_df(conn, sql, (int(limit),))
    return df.iloc[::-1].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Smoke test.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    c = init_db(":memory:")
    rid = insert_telemetry(
        c,
        {
            "ts": 1_700_000_000_000,
            "temperature": 22.5,
            "humidity": 45.2,
            "co2": 650.0,
            "motion": 1,
            "room_id": "room1",
        },
    )
    pid = insert_prediction(c, 1_700_000_000_000, "medium", "rule_baseline_v1")
    print(f"Inserted telemetry id={rid}, prediction id={pid}")
    print("Recent telemetry:")
    print(query_recent_telemetry(c, minutes=10**9).to_string(index=False))
    print("Recent predictions:")
    print(query_recent_predictions(c, minutes=10**9).to_string(index=False))
    close_all()