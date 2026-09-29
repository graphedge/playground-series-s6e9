#!/usr/bin/env python3
"""
Baseline models for playground-series-s6e9 (EV Purchase Prediction).

5-fold StratifiedKFold, seed=42:
  - Logistic Regression (class_weight='balanced')
  - LightGBM (scale_pos_weight from class counts)
  - LightGBM with simple feature engineering

Outputs artifacts/baseline_summary.json with OOF ROC-AUC and PR-AUC.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb

# Paths
DATA_DIR = Path("data")
TRAIN_PATH = DATA_DIR / "train.csv"
ARTIFACTS_DIR = Path("artifacts")
OUTPUT_PATH = ARTIFACTS_DIR / "baseline_summary.json"

SEED = 42
N_FOLDS = 5


def load_data():
    """Load train.csv and separate features from target."""
    if not TRAIN_PATH.exists():
        print(f"Error: {TRAIN_PATH} not found.")
        print("Run scripts/01_download.sh first.")
        sys.exit(1)
    
    df = pd.read_csv(TRAIN_PATH)
    print(f"Loaded {TRAIN_PATH}: {df.shape}")
    
    # Target
    target_col = "Will_Buy_EV"
    if target_col not in df.columns:
        print(f"Error: Target column '{target_col}' not found.")
        sys.exit(1)
    
    y = df[target_col].values
    
    # Features: drop ID and target
    drop_cols = ["id", target_col]
    X = df.drop(columns=drop_cols)
    
    print(f"Features: {X.shape[1]} columns")
    print(f"Target balance: {y.mean():.4f} positive class")
    
    return X, y, df


def engineer_features(X):
    """Simple feature engineering: charging_stations_total, income_per_commute."""
    X_fe = X.copy()
    
    # Sum of all charging station columns
    charging_cols = [
        "Charging_Stations_Near_Home",
        "Charging_Stations_Near_Work",
    ]
    if all(c in X_fe.columns for c in charging_cols):
        X_fe["charging_stations_total"] = X_fe[charging_cols].sum(axis=1)
    
    # Income per commute (avoid division by zero)
    if "Annual_Income_USD" in X_fe.columns and "Daily_Commute_km" in X_fe.columns:
        X_fe["income_per_commute"] = X_fe["Annual_Income_USD"] / (X_fe["Daily_Commute_km"] + 1e-6)
    
    return X_fe


def cv_logistic(X, y):
    """5-fold CV for Logistic Regression with balanced class weights."""
    print("\n=== Logistic Regression (balanced) ===")
    
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof_preds = np.zeros(len(y))
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Standardize
        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_val_sc = scaler.transform(X_val)
        
        # Train
        model = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=SEED,
            n_jobs=-1,
        )
        model.fit(X_train_sc, y_train)
        
        # Predict
        oof_preds[val_idx] = model.predict_proba(X_val_sc)[:, 1]
        
        fold_auc = roc_auc_score(y_val, oof_preds[val_idx])
        print(f"  Fold {fold}: ROC-AUC = {fold_auc:.4f}")
    
    oof_auc = roc_auc_score(y, oof_preds)
    oof_pr_auc = average_precision_score(y, oof_preds)
    
    print(f"OOF ROC-AUC: {oof_auc:.4f}")
    print(f"OOF PR-AUC:  {oof_pr_auc:.4f}")
    
    return oof_auc, oof_pr_auc


def cv_lightgbm(X, y, scale_pos_weight, label="LightGBM"):
    """5-fold CV for LightGBM with scale_pos_weight."""
    print(f"\n=== {label} ===")
    
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    oof_preds = np.zeros(len(y))
    feature_importances = []
    
    params = {
        "objective": "binary",
        "metric": "auc",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "scale_pos_weight": scale_pos_weight,
        "random_state": SEED,
        "verbose": -1,
    }
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
        )
        
        oof_preds[val_idx] = model.predict(X_val, num_iteration=model.best_iteration)
        
        fold_auc = roc_auc_score(y_val, oof_preds[val_idx])
        print(f"  Fold {fold}: ROC-AUC = {fold_auc:.4f} (iterations={model.best_iteration})")
        
        # Collect feature importances
        feature_importances.append(model.feature_importance(importance_type="gain"))
    
    oof_auc = roc_auc_score(y, oof_preds)
    oof_pr_auc = average_precision_score(y, oof_preds)
    
    print(f"OOF ROC-AUC: {oof_auc:.4f}")
    print(f"OOF PR-AUC:  {oof_pr_auc:.4f}")
    
    # Average feature importances
    avg_importances = np.mean(feature_importances, axis=0)
    top_features = sorted(
        zip(X.columns, avg_importances),
        key=lambda x: x[1],
        reverse=True,
    )[:12]
    
    print("Top features:")
    for feat, imp in top_features:
        print(f"  {feat}: {imp:.0f}")
    
    return oof_auc, oof_pr_auc, dict(top_features)


def main():
    X, y, df_full = load_data()
    
    # Class counts
    n_pos = y.sum()
    n_neg = len(y) - n_pos
    scale_pos_weight = n_neg / n_pos
    
    print(f"\nClass counts: Yes={n_pos}, No={n_neg}")
    print(f"scale_pos_weight: {scale_pos_weight:.4f}")
    
    # 1. Logistic baseline
    logistic_auc, logistic_pr_auc = cv_logistic(X, y)
    
    # 2. LightGBM raw
    lgb_auc, lgb_pr_auc, lgb_importances = cv_lightgbm(
        X, y, scale_pos_weight, label="LightGBM (raw)"
    )
    
    # 3. LightGBM with feature engineering
    X_fe = engineer_features(X)
    lgb_fe_auc, lgb_fe_pr_auc, lgb_fe_importances = cv_lightgbm(
        X_fe, y, scale_pos_weight, label="LightGBM (FE)"
    )
    
    # Save results
    results = {
        "cv": f"StratifiedKFold {N_FOLDS} seed={SEED}",
        "metric": "ROC-AUC (+ PR-AUC)",
        "class_balance": {
            "yes": int(n_pos),
            "no": int(n_neg),
            "scale_pos_weight": float(scale_pos_weight),
        },
        "models": {
            "logistic_raw_balanced": {
                "oof_auc": float(logistic_auc),
                "oof_pr_auc": float(logistic_pr_auc),
            },
            "lightgbm_raw_spw": {
                "oof_auc": float(lgb_auc),
                "oof_pr_auc": float(lgb_pr_auc),
            },
            "lightgbm_fe_spw": {
                "oof_auc": float(lgb_fe_auc),
                "oof_pr_auc": float(lgb_fe_pr_auc),
                "extra_features": ["charging_stations_total", "income_per_commute"],
            },
        },
        "submitted_to_kaggle": False,
        "top_features": {k: float(v) for k, v in lgb_fe_importances.items()},
    }
    
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n=== Summary ===")
    print(f"Logistic (balanced): {logistic_auc:.4f} ROC-AUC, {logistic_pr_auc:.4f} PR-AUC")
    print(f"LightGBM (raw):      {lgb_auc:.4f} ROC-AUC, {lgb_pr_auc:.4f} PR-AUC")
    print(f"LightGBM (FE):       {lgb_fe_auc:.4f} ROC-AUC, {lgb_fe_pr_auc:.4f} PR-AUC")
    print(f"\nResults written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
