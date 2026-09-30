#!/usr/bin/env python3
"""Spec 002 P0 LightGBM smoke-test viability gate (25% stratified sample)."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

FULL_BASELINE_AUC = 0.9416479457702023
SAMPLE_FRAC = 0.25
SEED = 42
N_FOLDS = 3
EARLY_STOPPING = 30

COMMON_PARAMS = {
    "objective": "binary",
    "metric": "auc",
    "learning_rate": 0.05,
    "n_estimators": 300,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": SEED,
    "n_jobs": -1,
    "verbosity": -1,
}


def encode_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Encode categoricals consistently; return X and feature names in order."""
    X = df.copy()
    # Explicit ordered encodings for constraint columns
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

    feature_cols = [c for c in X.columns]
    return X[feature_cols], feature_cols


def monotone_constraints(feature_cols: list[str]) -> list[int]:
    cons = []
    for c in feature_cols:
        if c == "Subsidy_Available":
            cons.append(1)
        elif c == "Range_Anxiety_Level":
            cons.append(-1)
        else:
            cons.append(0)
    return cons


def oof_cv(
    X: pd.DataFrame,
    y: np.ndarray,
    params: dict,
    name: str,
) -> dict:
    """3-fold stratified OOF ROC-AUC and PR-AUC."""
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof = np.zeros(len(y), dtype=float)
    fold_aucs = []
    fold_pras = []
    n_trees = []
    crash = None
    t0 = time.time()
    try:
        for fold, (tr_idx, va_idx) in enumerate(skf.split(X, y)):
            X_tr, X_va = X.iloc[tr_idx], X.iloc[va_idx]
            y_tr, y_va = y[tr_idx], y[va_idx]
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
            pred = model.predict_proba(X_va)[:, 1]
            oof[va_idx] = pred
            fold_aucs.append(float(roc_auc_score(y_va, pred)))
            fold_pras.append(float(average_precision_score(y_va, pred)))
            best = getattr(model, "best_iteration_", None)
            n_trees.append(int(best) if best is not None else params.get("n_estimators", 300))
        oof_auc = float(roc_auc_score(y, oof))
        oof_pr = float(average_precision_score(y, oof))
        status = "ok"
    except Exception as e:
        crash = f"{type(e).__name__}: {e}"
        status = "crash"
        oof_auc = None
        oof_pr = None
        traceback.print_exc()
    elapsed = time.time() - t0
    return {
        "name": name,
        "status": status,
        "crash": crash,
        "oof_auc": oof_auc,
        "oof_pr_auc": oof_pr,
        "fold_aucs": fold_aucs,
        "fold_pr_aucs": fold_pras,
        "best_iterations": n_trees,
        "elapsed_sec": round(elapsed, 2),
        "params": {k: v for k, v in params.items() if k != "monotone_constraints"},
        "monotone_constraints": params.get("monotone_constraints"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Spec 002 P0 smoke-gate: capacity + monotone viability test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variable fallback:
  SMOKE_TRAIN_CSV — path to train.csv (if --train-csv not provided)

Example usage:
  python scripts/smoke_p0_capacity.py --train-csv data/train.csv --out-dir data/smoke_out
  SMOKE_TRAIN_CSV=data/train.csv python scripts/smoke_p0_capacity.py --out-dir data/smoke_out
        """,
    )
    parser.add_argument(
        "--train-csv",
        type=Path,
        help="Path to train.csv (can also set SMOKE_TRAIN_CSV env var)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/smoke_out"),
        help="Output directory for results (default: data/smoke_out)",
    )
    args = parser.parse_args()

    train_path = args.train_csv or os.environ.get("SMOKE_TRAIN_CSV")
    if not train_path:
        print("Error: train.csv path not provided.", file=sys.stderr)
        print("  Use --train-csv PATH or set SMOKE_TRAIN_CSV env var.", file=sys.stderr)
        sys.exit(1)

    train_path = Path(train_path)
    if not train_path.exists():
        print(f"Error: {train_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {train_path} ...")
    df = pd.read_csv(train_path)
    assert "id" in df.columns
    y_raw = df["Will_Buy_EV"].map({"Yes": 1, "No": 0}).astype(int)
    X_full = df.drop(columns=["id", "Will_Buy_EV"])

    anx_vals = sorted(X_full["Range_Anxiety_Level"].dropna().unique().tolist())
    print("Range_Anxiety_Level uniques:", anx_vals)
    assert set(anx_vals) == {"Low", "Medium", "High"}

    X_enc, feature_cols = encode_frame(X_full)
    y = y_raw.values

    print(f"Full rows={len(X_enc)}, pos_rate={y.mean():.6f}")
    print("Features:", feature_cols)

    X_s, _, y_s, _ = train_test_split(
        X_enc,
        y,
        train_size=SAMPLE_FRAC,
        stratify=y,
        random_state=SEED,
    )
    X_s = X_s.reset_index(drop=True)
    y_s = np.asarray(y_s)
    n_pos = int(y_s.sum())
    n_neg = int(len(y_s) - n_pos)
    spw = n_neg / n_pos
    print(f"Smoke sample n={len(y_s)}, pos={n_pos}, neg={n_neg}, scale_pos_weight={spw:.6f}")

    mono = monotone_constraints(feature_cols)
    print("monotone_constraints:", list(zip(feature_cols, mono)))

    params_a = {
        **COMMON_PARAMS,
        "max_depth": 6,
        "num_leaves": 31,
        "scale_pos_weight": spw,
    }
    params_b = {
        **COMMON_PARAMS,
        "max_depth": 8,
        "num_leaves": 64,
        "scale_pos_weight": spw,
    }
    params_c = {
        **params_b,
        "monotone_constraints": mono,
    }

    results = {}
    print("\n=== Model A (baseline-ish capacity) ===")
    results["A"] = oof_cv(X_s, y_s, params_a, "A_baseline_ish")
    print(results["A"])

    print("\n=== Model B (capacity smoke) ===")
    results["B"] = oof_cv(X_s, y_s, params_b, "B_capacity")
    print(results["B"])

    print("\n=== Model C (capacity + monotone) ===")
    results["C"] = oof_cv(X_s, y_s, params_c, "C_capacity_monotone")
    print(results["C"])

    auc_a = results["A"]["oof_auc"]
    auc_b = results["B"]["oof_auc"]
    auc_c = results["C"]["oof_auc"]
    crashes = {
        k: results[k]["crash"] for k in ("A", "B", "C") if results[k]["crash"]
    }

    delta_ba = None if auc_a is None or auc_b is None else abs(auc_b - auc_a)
    delta_ca = None if auc_a is None or auc_c is None else abs(auc_c - auc_a)
    signed_ba = None if auc_a is None or auc_b is None else (auc_b - auc_a)
    signed_ca = None if auc_a is None or auc_c is None else (auc_c - auc_a)

    a_ok = results["A"]["status"] == "ok"
    b_ok = results["B"]["status"] == "ok"
    c_ok = results["C"]["status"] == "ok"

    if not a_ok or not b_ok:
        gate = "STOP"
        rationale = (
            "STOP: crash blocked capacity path "
            f"(A={results['A']['status']}, B={results['B']['status']}, crashes={crashes})."
        )
    else:
        moved_b = delta_ba is not None and delta_ba > 0.0001
        moved_c = c_ok and delta_ca is not None and delta_ca > 0.0001
        if moved_b or (not moved_b and moved_c):
            gate = "PASS"
            if moved_b:
                rationale = (
                    f"PASS: A/B trained cleanly; |AUC_B-AUC_A|={delta_ba:.6f} > 0.0001 "
                    f"(signed B-A={signed_ba:+.6f}); capacity path shows movement on sample."
                )
            else:
                rationale = (
                    f"PASS: B flat vs A (|Δ|={delta_ba:.6f}) but C moves vs A "
                    f"(|Δ|={delta_ca:.6f}, signed={signed_ca:+.6f})."
                )
        else:
            gate = "STOP"
            rationale = (
                f"STOP: dead flat — |AUC_B-AUC_A|={delta_ba} ≤ 0.0001 and "
                f"|AUC_C-AUC_A|={delta_ca} ≤ 0.0001 (or C crashed)."
            )

    payload = {
        "sample_frac": SAMPLE_FRAC,
        "n_rows": int(len(y_s)),
        "n_pos": n_pos,
        "n_neg": n_neg,
        "pos_rate": float(y_s.mean()),
        "scale_pos_weight": float(spw),
        "seed": SEED,
        "folds": N_FOLDS,
        "early_stopping_rounds": EARLY_STOPPING,
        "feature_cols": feature_cols,
        "full_data_baseline_auc": FULL_BASELINE_AUC,
        "models": {
            "A": results["A"],
            "B": results["B"],
            "C": results["C"],
        },
        "deltas": {
            "abs_B_minus_A": delta_ba,
            "abs_C_minus_A": delta_ca,
            "signed_B_minus_A": signed_ba,
            "signed_C_minus_A": signed_ca,
            "B_minus_full_baseline": None if auc_b is None else (auc_b - FULL_BASELINE_AUC),
            "note": (
                "Primary gate is same-sample A vs B/C. Sample OOF is not directly "
                "comparable to full-data 5-fold baseline 0.94165."
            ),
        },
        "crashes": crashes,
        "gate": gate,
        "rationale": rationale,
    }

    json_path = out_dir / "smoke_p0_result.json"
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nWrote {json_path}")

    md_path = out_dir / "SMOKE.md"
    def fmt(x):
        return "n/a" if x is None else f"{x:.6f}"

    md = f"""# Spec 002 P0 LightGBM Smoke Gate

**Decision: {gate}**

{rationale}

## Setup
- Sample: {SAMPLE_FRAC:.0%} stratified (`train_test_split`, `random_state={SEED}`) → n={len(y_s)} rows
- CV: StratifiedKFold n_splits={N_FOLDS}, shuffle=True, random_state={SEED}
- Target pos rate (sample): {y_s.mean():.4%} | scale_pos_weight={spw:.4f}
- Full-data baseline (context only): ROC-AUC {FULL_BASELINE_AUC:.6f}

## OOF scores (smoke sample)

| Model | ROC-AUC | PR-AUC | Δ ROC vs A | Status |
|-------|---------|--------|------------|--------|
| A baseline-ish (depth=6, leaves=31) | {fmt(auc_a)} | {fmt(results['A']['oof_pr_auc'])} | — | {results['A']['status']} |
| B capacity (depth=8, leaves=64) | {fmt(auc_b)} | {fmt(results['B']['oof_pr_auc'])} | {fmt(signed_ba)} | {results['B']['status']} |
| C capacity + monotone | {fmt(auc_c)} | {fmt(results['C']['oof_pr_auc'])} | {fmt(signed_ca)} | {results['C']['status']} |

## Gate rule
- PASS if A and B train without crash AND (|AUC_B−AUC_A| > 0.0001 OR C clearly moves vs A).
- STOP if capacity path crashes OR both B and C are dead-flat vs A (≤ 0.0001).

## Crashes
{json.dumps(crashes, indent=2) if crashes else "None"}

## Artifacts
- `{json_path}`
"""
    md_path.write_text(md)
    print(f"Wrote {md_path}")
    print("\n=== GATE:", gate, "===")
    print(rationale)


if __name__ == "__main__":
    main()
