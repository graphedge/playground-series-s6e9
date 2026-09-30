# Results (local, not submitted)

Competition: [playground-series-s6e9](https://www.kaggle.com/competitions/playground-series-s6e9) — Predicting Electric Vehicle Purchases.

Metric: ROC-AUC (also track PR-AUC). Target `Will_Buy_EV` ~17.5% Yes. No missing values in train.

## Baselines (5-fold StratifiedKFold, seed=42)

| Model | OOF ROC-AUC | OOF PR-AUC |
|-------|------------:|----------:|
| Logistic (balanced) raw | 0.9381 | 0.7410 |
| LightGBM raw (`scale_pos_weight`) | **0.9416** | **0.7555** |
| LightGBM + charging_stations_total + income_per_commute | 0.9415 | 0.7548 |

FE did not beat raw LightGBM. Prefer the simpler raw model.

Top LightGBM importances (FE model): Annual_Income_USD, Daily_Commute_km, income_per_commute, Age, charging totals / near work/home, Environmental_Concern_Level, Range_Anxiety_Level.

`submitted_to_kaggle`: false — do not submit unless Brett asks.

Blend + calibration + threshold sweep may update this file later.

## Smoke gates

- [Spec 002 P0 smoke gate (capacity + monotone)](smoke/SMOKE.md) — **PASS**
