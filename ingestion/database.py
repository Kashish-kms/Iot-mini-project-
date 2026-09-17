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