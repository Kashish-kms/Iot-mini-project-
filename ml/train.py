"""Train the AIoT air-quality / occupancy risk classifiers.

Two models are produced:
  * ``RuleBasedClassifier`` — an explicit-threshold baseline (deterministic,
    fully interpretable; serves as the "human expert" floor).
  * ``RandomForestClassifier`` — scikit-learn ensemble with 200 trees.

Both models are saved with :mod:`joblib` under ``ml/models/``.

Labels (ground truth) are constructed DETERMINISTICALLY from the same
physics of the simulator, not from manual annotation — the simulator is the
label source of truth. This lets us evaluate how well each model can
rediscover the deterministic thresholds from the raw features alone.

If no ``features`` table exists in SQLite we fall back to generating a large
synthetic training dataset using the SensorGenerator across multiple distinct
``SCENARIO_SEED`` values. This way ``train.py`` is independently runnable
without running the whole docker-compose stack first.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ingestion import database as db
    from ingestion import preprocessing
    from simulator.config import Config
    from simulator.generator import SensorGenerator
else:
    from ingestion import database as db
    from ingestion import preprocessing
    from simulator.config import Config
    from simulator.generator import SensorGenerator


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ml/train] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ml.train")

MODELS_DIR = Path(__file__).resolve().parent / "models"
CLASSES: Tuple[str, ...] = ("low", "medium", "high")


FEATURE_COLUMNS: Tuple[str, ...] = (
    "temperature", "humidity", "co2", "motion",
    "temp_mean_5", "temp_std_5", "temp_mean_15", "temp_std_15",
    "hum_mean_5", "hum_std_5", "hum_mean_15", "hum_std_15",
    "co2_mean_5", "co2_std_5", "co2_mean_15", "co2_std_15",
    "temp_rate", "hum_rate", "co2_rate",
    "hour", "is_daytime",
)


def build_ground_truth_labels(df: pd.DataFrame) -> pd.Series:
    """3-class risk labels using the known simulator physics.

    high:   CO2 >= 1000 ppm  OR  temp >= 26 °C  OR  humidity outside [30, 60] %.
    medium: not high, and ( (rolling motion-3 mean >= 0.3 AND CO2 >= 600)
                            OR CO2 >= 800 ppm ).
    low:    everything else.
    """
    out = pd.Series("low", index=df.index, dtype="object")
    high = (
        (df["co2"] >= 1000.0)
        | (df["temperature"] >= 26.0)
        | (df["humidity"] < 30.0)
        | (df["humidity"] > 60.0)
    )
    motion_roll = df["motion"].rolling(window=3, min_periods=1).mean()
    medium = ~high & (((motion_roll >= 0.30) & (df["co2"] >= 600.0)) | (df["co2"] >= 800.0))
    out[medium] = "medium"
    out[high] = "high"
    return out


class RuleBasedClassifier(BaseEstimator, ClassifierMixin):
    """Sklearn-compatible fixed-threshold baseline.

    Uses per-row feature values only (no rolling motion mean access).
    This makes it a weaker oracle than the exact ground-truth function,
    which is appropriate for a baseline.
    """

    classes_ = np.array(CLASSES)

    def fit(self, X, y=None, **kw):
        if hasattr(X, "shape"):
            self.n_features_in_ = X.shape[1]
        return self

    def _as_df(self, X) -> pd.DataFrame:
        if hasattr(X, "columns"):
            return pd.DataFrame(X, copy=True)
        return pd.DataFrame(X, columns=list(FEATURE_COLUMNS[: X.shape[1]]))

    def predict(self, X) -> np.ndarray:
        df = self._as_df(X)
        out = np.array(["low"] * len(df), dtype=object)
        temp = df["temperature"].to_numpy()
        hum = df["humidity"].to_numpy()
        motion = df.get("motion", pd.Series(0.0, index=df.index)).to_numpy()
        co2_col = df.get("co2_mean_5", df.get("co2"))
        co2 = co2_col.to_numpy()

        high = (co2 >= 1000.0) | (temp >= 26.0) | (hum < 30.0) | (hum > 60.0)
        medium = ~high & (((motion >= 0.5) & (co2 >= 600.0)) | (co2 >= 800.0))
        out[medium] = "medium"
        out[high] = "high"
        return out


def _ensure_features_from_db(db_path: Optional[str]) -> Optional[pd.DataFrame]:
    db_path = db_path or os.environ.get("DB_PATH", "./data/iot.db")
    try:
        conn = db.init_db(db_path)
    except Exception:
        return None
    feats = db.query_all_features(conn)
    db.close_all()
    if feats is None or len(feats) < 50:
        return None
    return feats


def _synthetic_features_scenarios(
    scenarios: Tuple[int, ...] = (1, 2, 3, 4, 5, 6),
    windows_per_scenario: int = 7 * 24 * 60,
) -> pd.DataFrame:
    """Generate features using multiple SCENARIO_SEED values.

    Each scenario has different occupancy pattern characteristics. Every
    row is tagged with ``scenario_seed`` so evaluate.py can split by it.
    """
    scenario_dfs = []
    for seed in scenarios:
        log.info(
            f"Generating synthetic scenario seed={seed} "
            f"({windows_per_scenario} 1-min windows = ~{windows_per_scenario // 60}h)..."
        )
        cfg = Config.from_env({"SCENARIO_SEED": seed})
        start = 1_700_000_000_000 + int(seed) * 1000_000_000
        gen = SensorGenerator(cfg, start_epoch_ms=start)
        gen._override_room_id(cfg.ROOM_ID)
        rows = gen.generate_batch(windows_per_scenario)
        df_raw = pd.DataFrame(rows).rename(columns={"timestamp": "ts"})
        cleaned = preprocessing.remove_outliers_iqr(df_raw)
        rs = preprocessing.resample_fixed(cleaned)
        feats = preprocessing.engineer_features(rs)
        feats["scenario_seed"] = int(seed)
        scenario_dfs.append(feats)
    combined = pd.concat(scenario_dfs, ignore_index=True)
    combined = combined.sort_values("ts").reset_index(drop=True)
    return combined


def load_or_build_features(
    db_path: Optional[str] = None,
    force_synthetic: bool = False,
    scenarios: Tuple[int, ...] = (1, 2, 3, 4, 5, 6),
) -> Tuple[pd.DataFrame, pd.Series]:
    if not force_synthetic:
        feats = _ensure_features_from_db(db_path)
        if feats is not None:
            feats = feats.copy()
            n = len(feats)
            per = max(1, n // len(scenarios))
            feats["scenario_seed"] = [
                scenarios[min(len(scenarios) - 1, i // per)]
                for i in range(n)
            ]
            y = build_ground_truth_labels(feats)
            log.info(f"Loaded {n} rows from SQLite features table")
            return feats.reset_index(drop=True), y.reset_index(drop=True)
    feats = _synthetic_features_scenarios(scenarios=scenarios)
    y = build_ground_truth_labels(feats)
    log.info(
        f"Built synthetic dataset: {len(feats)} rows, "
        f"{feats['scenario_seed'].nunique()} scenarios"
    )
    return feats.reset_index(drop=True), y.reset_index(drop=True)


def _select_X(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in FEATURE_COLUMNS if c in df.columns]
    X = df[cols].copy()
    X = X.ffill().bfill().fillna(0.0)
    return X


@dataclass
class ModelMeta:
    model_version: str
    feature_columns: List[str]
    random_seed: int
    n_rows: int
    class_counts: Dict[str, int]


def train_and_save(
    db_path: Optional[str] = None,
    force_synthetic: bool = False,
    model_dir: Optional[Path] = None,
) -> Tuple[RuleBasedClassifier, RandomForestClassifier, ModelMeta]:
    model_dir = Path(model_dir or MODELS_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)
    df, y = load_or_build_features(db_path=db_path, force_synthetic=force_synthetic)
    X = _select_X(df)
    feature_cols = list(X.columns)
    seed = int(os.environ.get("RANDOM_SEED", "42"))

    rule = RuleBasedClassifier()
    rule.fit(X, y)

    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    rf.fit(X, y)
    rf.feature_names_in_ = np.array(feature_cols, dtype=object)

    meta = ModelMeta(
        model_version="v1",
        feature_columns=feature_cols,
        random_seed=seed,
        n_rows=len(df),
        class_counts={c: int((y == c).sum()) for c in CLASSES},
    )
    joblib.dump(rule, model_dir / "rule_baseline_v1.joblib")
    joblib.dump(rf, model_dir / "random_forest_v1.joblib")
    joblib.dump(asdict(meta), model_dir / "metadata_v1.joblib")
    log.info(
        f"Saved models to {model_dir}: rule_baseline_v1.joblib, "
        f"random_forest_v1.joblib (N={meta.n_rows}, classes={meta.class_counts})"
    )
    return rule, rf, meta


if __name__ == "__main__":
    force_synth = "--synthetic" in sys.argv
    _, _, meta = train_and_save(force_synthetic=force_synth)
    print()
    print("Training summary:")
    for k, v in asdict(meta).items():
        if isinstance(v, list):
            v = f"<{len(v)} feature columns>"
        print(f"  {k}: {v}")
