#!/usr/bin/env python3
"""Spec 003: raw LightGBM 5-fold OOF baseline → local Kaggle submission CSV.

Raw LGBM with integer-encoded categoricals, per-fold scale_pos_weight,
colsample_bytree/subsample 0.8, early stopping 30.
(Differs from scripts/03_baselines.py hyperparams; OOF sits near that baseline.)

Does NOT submit to Kaggle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

DATA_DIR = Path("data")
SEED = 42
N_FOLDS = 5
EARLY_STOPPING = 30

COMMON_PARAMS = {
    "objective": "binary",
    "metric": "auc",
    "learning_rate": 0.05,
    "n_estimators": 500,
    "max_depth": 6,
    "num_leaves": 31,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": SEED,
    "n_jobs": -1,
    "verbosity": -1,
}


def encode_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categoricals like smoke_p0_capacity.encode_frame."""
    X = df.copy()
    anxiety_map = {"Low": 0, "Medium": 1, "High": 2}
    subsidy_map = {"No": 0, "Yes": 1}
    X["Range_Anxiety_Level"] = X["Range_Anxiety_Level"].map(anxiety_map).astype(int)
    X["Subsidy_Available"] = X["Subsidy_Available"].map(subsidy_map).astype(int)

    other_cats = [
        "Gender",
        "City_Type",
        "Current_Car_Type",
        "Home_Charging_Possible",
    ]
    for col in other_cats:
        codes, _ = pd.factorize(X[col], sort=True)
        X[col] = codes.astype(int)
    return X


def encode_train_test(
    train_x: pd.DataFrame, test_x: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Encode train+test together so factorize codes are consistent."""
    n_train = len(train_x)
    combined = pd.concat([train_x, test_x], axis=0, ignore_index=True)
    encoded = encode_frame(combined)
    return encoded.iloc[:n_train].reset_index(drop=True), encoded.iloc[n_train:].reset_index(
        drop=True
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train-csv", type=Path, default=DATA_DIR / "train.csv")
    p.add_argument("--test-csv", type=Path, default=DATA_DIR / "test.csv")
    p.add_argument("--sample-csv", type=Path, default=DATA_DIR / "sample_submission.csv")
    p.add_argument(
        "--out-csv",
        type=Path,
        default=DATA_DIR / "submissions" / "submission_lgbm_raw_5fold.csv",
    )
    p.add_argument(
        "--out-meta",
        type=Path,
        default=DATA_DIR / "submissions" / "submission_lgbm_raw_5fold_meta.json",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading train={args.train_csv}")
    train = pd.read_csv(args.train_csv)
    print(f"Loading test={args.test_csv}")
    test = pd.read_csv(args.test_csv)
    sample = pd.read_csv(args.sample_csv)

    y = train["Will_Buy_EV"].map({"Yes": 1, "No": 0}).astype(int).values
    train_x = train.drop(columns=["id", "Will_Buy_EV"])
    test_ids = test["id"].values
    test_x = test.drop(columns=["id"])

    # Sanity: anxiety labels
    anx = sorted(train_x["Range_Anxiety_Level"].dropna().unique().tolist())
    assert set(anx) == {"Low", "Medium", "High"}, anx

    X_train, X_test = encode_train_test(train_x, test_x)
    feature_cols = list(X_train.columns)
    print(f"n_train={len(X_train)}, n_test={len(X_test)}, features={feature_cols}")

    # Global scale_pos_weight for reporting; per-fold uses fold train counts
    n_pos_all = int(y.sum())
    n_neg_all = int(len(y) - n_pos_all)
    spw_global = n_neg_all / n_pos_all
    print(f"pos={n_pos_all}, neg={n_neg_all}, scale_pos_weight≈{spw_global:.6f}")

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y), dtype=float)
    test_pred = np.zeros(len(X_test), dtype=float)
    fold_aucs: list[float] = []
    fold_pras: list[float] = []
    best_iterations: list[int] = []
    fold_spws: list[float] = []

    for fold, (tr_idx, va_idx) in enumerate(skf.split(X_train, y)):
        X_tr, X_va = X_train.iloc[tr_idx], X_train.iloc[va_idx]
        y_tr, y_va = y[tr_idx], y[va_idx]
        n_pos = int(y_tr.sum())
        n_neg = int(len(y_tr) - n_pos)
        spw = n_neg / n_pos
        fold_spws.append(float(spw))

        params = {**COMMON_PARAMS, "scale_pos_weight": spw}
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_tr,
            y_tr,
            eval_set=[(X_va, y_va)],
            callbacks=[
                lgb.early_stopping(EARLY_STOPPING, verbose=False),
                lgb.log_evaluation(period=0),
            ],
        )
        va_pred = model.predict_proba(X_va)[:, 1]
        oof[va_idx] = va_pred
        test_pred += model.predict_proba(X_test)[:, 1] / N_FOLDS

        fold_auc = float(roc_auc_score(y_va, va_pred))
        fold_pra = float(average_precision_score(y_va, va_pred))
        fold_aucs.append(fold_auc)
        fold_pras.append(fold_pra)
        best = getattr(model, "best_iteration_", None)
        n_trees = int(best) if best is not None else params["n_estimators"]
        best_iterations.append(n_trees)
        print(
            f"Fold {fold}: AUC={fold_auc:.6f} PR-AUC={fold_pra:.6f} "
            f"best_iter={n_trees} spw={spw:.4f}"
        )

    oof_auc = float(roc_auc_score(y, oof))
    oof_pr_auc = float(average_precision_score(y, oof))
    print(f"\nOOF ROC-AUC={oof_auc:.10f}")
    print(f"OOF PR-AUC={oof_pr_auc:.10f}")
    print(f"Fold AUCs={fold_aucs}")

    # Align submission to sample_submission row order/ids
    pred_by_id = dict(zip(test_ids.tolist(), test_pred.tolist()))
    sample_ids = sample["id"].values
    missing = [i for i in sample_ids if i not in pred_by_id]
    if missing:
        raise RuntimeError(f"{len(missing)} sample ids missing from test preds, e.g. {missing[:5]}")
    ordered_probs = np.array([pred_by_id[i] for i in sample_ids], dtype=float)

    if not np.isfinite(ordered_probs).all():
        raise RuntimeError("Non-finite probabilities in submission")
    if not ((ordered_probs > 0) & (ordered_probs < 1)).all():
        lo, hi = float(ordered_probs.min()), float(ordered_probs.max())
        raise RuntimeError(f"Probs not strictly in (0,1): min={lo} max={hi}")

    sub = pd.DataFrame({"id": sample_ids, "Will_Buy_EV": ordered_probs})
    sub.to_csv(args.out_csv, index=False)
    print(f"Wrote {args.out_csv} rows={len(sub)}")

    meta = {
        "oof_auc": oof_auc,
        "oof_pr_auc": oof_pr_auc,
        "fold_aucs": fold_aucs,
        "fold_pr_aucs": fold_pras,
        "best_iterations": best_iterations,
        "fold_scale_pos_weights": fold_spws,
        "scale_pos_weight_global": float(spw_global),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_submission_rows": int(len(sub)),
        "feature_cols": feature_cols,
        "params": {**COMMON_PARAMS, "scale_pos_weight": "n_neg/n_pos per fold train"},
        "early_stopping_rounds": EARLY_STOPPING,
        "cv": f"StratifiedKFold {N_FOLDS} seed={SEED}",
        "baseline_reference_oof_auc": 0.9416479457702023,
        "submitted_to_kaggle": False,
        "message_suggestion": "lgbm raw 5fold",
        "out_csv": str(args.out_csv),
    }
    with open(args.out_meta, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {args.out_meta}")
    print("submitted_to_kaggle=false (no upload performed)")


if __name__ == "__main__":
    main()
