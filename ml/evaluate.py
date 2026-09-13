"""Evaluate the two trained AIoT classifiers.

Split strategy
--------------
Rows are grouped by ``scenario_seed`` (groups created by ``train.py``).
One or more entire scenario groups are held out as the TEST set — we NEVER
do a row-level random shuffle. This tests whether the RandomForest
generalizes to unseen occupancy patterns.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from ml.train import (
        CLASSES,
        RuleBasedClassifier,
        _select_X,
        build_ground_truth_labels,
        load_or_build_features,
        MODELS_DIR,
        train_and_save,
    )
else:
    from .train import (
        CLASSES,
        RuleBasedClassifier,
        _select_X,
        build_ground_truth_labels,
        load_or_build_features,
        MODELS_DIR,
        train_and_save,
    )


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ml/evaluate] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("ml.eval")


def split_by_scenario(
    df: pd.DataFrame,
    y: pd.Series,
    train_scenarios: Tuple[int, ...],
    test_scenarios: Tuple[int, ...],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    train_mask = df["scenario_seed"].isin(train_scenarios)
    test_mask = df["scenario_seed"].isin(test_scenarios)
    return (
        df.loc[train_mask].reset_index(drop=True),
        df.loc[test_mask].reset_index(drop=True),
        y.loc[train_mask].reset_index(drop=True),
        y.loc[test_mask].reset_index(drop=True),
    )


def _metrics(y_true, y_pred) -> Dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def _confusion_df(y_true, y_pred) -> pd.DataFrame:
    cm = confusion_matrix(y_true, y_pred, labels=list(CLASSES))
    return pd.DataFrame(
        cm,
        index=[f"true_{c}" for c in CLASSES],
        columns=[f"pred_{c}" for c in CLASSES],
    )


def run_evaluation(
    model_dir: Path = MODELS_DIR,
    force_synthetic: bool = False,
) -> pd.DataFrame:
    model_rule = model_dir / "rule_baseline_v1.joblib"
    model_rf = model_dir / "random_forest_v1.joblib"
    if not (model_rule.exists() and model_rf.exists()):
        log.warning("Saved models not found — running train_and_save first.")
        train_and_save(force_synthetic=force_synthetic)

    meta = joblib.load(model_dir / "metadata_v1.joblib")
    df, y = load_or_build_features(force_synthetic=force_synthetic)
    if "scenario_seed" not in df.columns:
        n = len(df)
        scenarios = [1, 2, 3, 4, 5, 6]
        per = max(1, n // len(scenarios))
        df["scenario_seed"] = [
            scenarios[min(len(scenarios) - 1, i // per)] for i in range(n)
        ]

    unique_scenarios = sorted(int(s) for s in df["scenario_seed"].unique().tolist())
    if len(unique_scenarios) >= 2:
        train_sc = tuple(unique_scenarios[:-1])
        test_sc = (unique_scenarios[-1],)
    else:
        half = max(1, len(unique_scenarios) // 2)
        train_sc = tuple(unique_scenarios[:half])
        test_sc = tuple(unique_scenarios[half:])
        if not test_sc:
            test_sc = train_sc

    log.info(
        f"Seed-based scenario split: train={train_sc} (will learn on {len(df[df['scenario_seed'].isin(train_sc)])} rows), "
        f"test={test_sc} ({len(df[df['scenario_seed'].isin(test_sc)])} rows)"
    )

    # Disjointness sanity: assert no overlap in rows by index between train/test DF pairs below.

    train_df, test_df, y_train, y_test = split_by_scenario(df, y, train_sc, test_sc)
    X_tr = _select_X(train_df)
    X_te = _select_X(test_df)

    # Sanity: train rows must not contain any test scenario seeds.
    assert not set(train_df["scenario_seed"].unique()) & set(test_df["scenario_seed"].unique()), (
        "Train/test scenario seeds overlap — split invalid!"
    )

    rule = RuleBasedClassifier()
    rule.fit(X_tr, y_train)

    rf = RandomForestClassifier(
        n_estimators=200,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=meta["random_seed"],
        n_jobs=-1,
    )
    rf.fit(X_tr, y_train)
    rf.feature_names_in_ = np.array(list(X_tr.columns), dtype=object)

    comparison_rows = []
    for name, model in [("RuleBased", rule), ("RandomForest", rf)]:
        for split_name, X, y_true in [
            ("Train", X_tr, y_train),
            ("Test", X_te, y_test),
        ]:
            if len(X) == 0:
                continue
            y_pred = model.predict(X)
            m = _metrics(y_true, y_pred)
            log.info(
                f"[{name}] {split_name:>5} — accuracy={m['accuracy']:.4f}, "
                f"f1_macro={m['f1_macro']:.4f}, f1_weighted={m['f1_weighted']:.4f}"
            )
            if split_name == "Test":
                comparison_rows.append(
                    {
                        "Model": name,
                        "Accuracy": m["accuracy"],
                        "F1-macro": m["f1_macro"],
                        "F1-weighted": m["f1_weighted"],
                    }
                )
                log.info(f"Confusion matrix — {name} Test:")
                for line in str(_confusion_df(y_true, y_pred)).splitlines():
                    log.info("  " + line)

    comp = pd.DataFrame(comparison_rows, columns=["Model", "Accuracy", "F1-macro", "F1-weighted"])
    comp = comp.set_index("Model")
    print()
    print("=" * 64)
    print("Model comparison (TEST set, scenario-split, no row shuffle):")
    print("=" * 64)
    with pd.option_context("display.precision", 4, "display.width", 120):
        print(comp.to_string())
    print("=" * 64)
    return comp.reset_index()


if __name__ == "__main__":
    force_synth = "--synthetic" in sys.argv
    comp = run_evaluation(force_synthetic=force_synth)
    if (comp["Accuracy"] < 0.5).any():
        log.warning("One or more models have accuracy <0.5; check data diversity.")
        sys.exit(2)
