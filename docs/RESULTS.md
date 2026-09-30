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

**Interaction drip**: Tested 7 feature interactions (env×anxiety, subsidy×anxiety, subsidy×home, city×subsidy, income tercile×subsidy, commute tercile×anxiety, cars×anxiety). OOF deltas flat (~±0.00003) vs 0.9416 raw baseline; tree models already capture these effects. EDA purchase-rate heatmaps for storytelling/intuition in [INTERACTION_GRAPHS.md](./INTERACTION_GRAPHS.md) (also [HTML gallery](./figures/interactions/interactions_gallery.html)).

`submitted_to_kaggle`: false — do not submit unless Brett asks.

Blend + calibration + threshold sweep may update this file later.

---

Feature interaction candidates for brute-force testing: [INTERACTION_CANDIDATES.md](./INTERACTION_CANDIDATES.md)

## Smoke gates

- [Spec 002 P0 smoke gate (capacity + monotone)](smoke/SMOKE.md) — **PASS** (viable to plan; sample scores slightly worse, not an improvement)

---

Competition work summary: [../reports/COMPETITION_SUMMARY.md](../reports/COMPETITION_SUMMARY.md)
