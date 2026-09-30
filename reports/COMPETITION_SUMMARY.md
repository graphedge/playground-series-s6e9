# Playground Series S6E9 — Competition Work Summary

**Competition:** [playground-series-s6e9](https://www.kaggle.com/competitions/playground-series-s6e9) — Predicting Electric Vehicle Purchases  
**Metric:** ROC-AUC (PR-AUC tracked locally)  
**Target:** `Will_Buy_EV` (~17.5% Yes; imbalanced)  
**Date covered:** 2026-09-29 – 2026-09-30  
**Repo policy:** Competition CSVs stay out of git; submission CSVs are gitignored.

This report summarizes modeling, submission, and selection decisions for the public write-up. Out-of-fold (OOF) scores and methodology are shared; Kaggle submission IDs, account handles, and local machine paths are omitted on purpose.

---

## 1. Context and baselines

Earlier work established:

| Model | OOF ROC-AUC | OOF PR-AUC | Notes |
|-------|------------:|----------:|-------|
| Logistic (balanced), raw features | ~0.9381 | ~0.7410 | Baseline |
| LightGBM raw (`scale_pos_weight`) | **~0.9416** | **~0.7555** | Preferred simple model |
| LightGBM + `charging_stations_total` + `income_per_commute` | ~0.9415 | ~0.7548 | FE did not beat raw |

Feature-interaction drips (env/subsidy/city/income/commute/cars × anxiety or charging-related pairs) were **flat** vs raw LightGBM (OOF deltas ~±0.00003). Tree models already capture those effects; interaction heatmaps remain useful for EDA storytelling only.

Standing rule: no Kaggle upload unless explicitly approved.

---

## 2. Spec 003 entry — single-seed raw LightGBM

Built a dedicated **5-fold StratifiedKFold** (fold seed 42) raw LightGBM trainer for the competition entry format (`id`, `Will_Buy_EV` probabilities).

**Recipe (high level):**

- Features: Age, Annual_Income_USD, Daily_Commute_km, Number_of_Cars_Owned, Charging_Stations_Near_Home/Work, Environmental_Concern_Level, plus factorized/ordinal categoricals (Gender, City_Type, Current_Car_Type, Home_Charging_Possible, Subsidy_Available, Range_Anxiety_Level with Low/Medium/High → 0/1/2).
- Params: binary objective, AUC metric, lr 0.05, max_depth 6, num_leaves 31, subsample/colsample 0.8, up to 500 estimators, early stopping 30, `scale_pos_weight` = n_neg/n_pos per fold train, model `random_state=42`.
- Test predictions: average of fold models.

| Metric | Value |
|--------|------:|
| OOF ROC-AUC | **0.94175** |
| OOF PR-AUC | **0.75568** |
| Public leaderboard (after submit) | **0.94151** (~rank ~2423 at score time) |

Submitted under message **`lgbm raw 5fold`** after explicit approval. That day still had remaining daily submit quota after this upload.

---

## 3. Lift attempts after public score 0.94151

Goal: move public rank without more feature crosses (already flat).

### 3.1 Logistic × LightGBM CV-weighted blend

Swept blend weight on OOF probabilities. Best weight was **w = 1.0** (pure LightGBM) → **+0** vs raw LGBM. Abandoned as a lift path; artifact kept locally only (not submitted).

### 3.2 Five-seed raw LightGBM bag (chosen lift)

Same CV folds (StratifiedKFold seed 42 for all runs so OOF rows align). Trained model seeds **42–46**, bagged by averaging OOF and test probability vectors.

| Seed | OOF ROC-AUC |
|-----:|------------:|
| 42 | 0.941751 |
| 43 | 0.941764 |
| 44 | 0.941734 |
| 45 | 0.941732 |
| 46 | 0.941751 |
| **Bag mean** | **0.941880** |

| Comparison | Δ OOF ROC-AUC |
|------------|--------------:|
| Bag − seed-42 single | **+0.00013** |
| Bag − seed-42 PR-AUC | +0.00067 |

This was the best local lift found. Submitted under message **`lgbm raw 5seed bag`** after explicit approval. At last check the public score was still **pending**; daily quota after that upload was **8 submissions remaining** that day. Guidance at submit time: if the bag's public score beats the single-seed **0.94151**, prefer selecting the bag on the Submissions tab (Playground still allows two final picks — see §5).

### 3.3 CatBoost experiment (dead end)

**Install:** CatBoost added to the working Python environment (v1.2.x class).

**Setup:**

- Same 5-fold StratifiedKFold (seed 42).
- Native `cat_features` on object columns (no manual encode for CatBoost).
- Params aligned in spirit with LGBM: Logloss / AUC, lr 0.05, depth 6, 500 iterations, early stopping 30, `scale_pos_weight` per fold, `random_seed=42`.
- Comparison LGBM OOF for the blend: **retrained single-seed** raw LGBM matching the Spec 003 recipe (5-seed bag OOF arrays were not reused for this sweep).

**Results:**

| Model / blend | OOF ROC-AUC | Notes |
|---------------|------------:|-------|
| CatBoost alone | **0.94130** | Below single-seed LGBM |
| Best blend `w·LGBM + (1−w)·CatBoost` | **0.94176** at **w = 0.88** (88% LGBM / 12% CatBoost) | |
| Δ vs single-seed LGBM | **+0.000007** | Noise-level |
| Reference 5-seed bag OOF | **0.94188** | Bag already better than this blend |

**Verdict:** Dead end relative to the 5-seed bag's **+0.00013**. **No Kaggle submission** was made from the CatBoost or LGBM×CatBoost blend artifacts.

---

## 4. Submissions timeline (redacted IDs)

| Order | Description | OOF ROC-AUC | Public LB | Status notes |
|------:|-------------|------------:|----------:|--------------|
| 1 | `lgbm raw 5fold` (single seed) | 0.94175 | **0.94151** | Scored; ~rank ~2423 at first look |
| 2 | `lgbm raw 5seed bag` | 0.94188 | *pending at last check* | Uploaded; waiting on public score |

Submission reference numbers and account/team names are intentionally not recorded here.

---

## 5. Final selection

Both submissions were marked for final scoring:

- Playground Series allows **two** selected submissions.
- Private leaderboard uses the **better** of the two selected entries.

Selecting both the single-seed entry and the 5-seed bag is valid and hedges until the bag's public score settles.

---

## 6. Open threads

1. **5-seed bag public score** — still pending at last check; confirm LB and rank once scored.
2. **Selection** — both entries marked; revisit only if a later model clearly dominates and a new submit is approved.
3. **Repo hygiene** — Spec 003 submission script / docs may still be landing via open PR(s); keep competition and submission CSVs out of git.
4. **Further modeling** — CatBoost blend and logistic blend are closed as lift paths; further work (e.g. XGBoost) only if explicitly requested.
5. **No unsolicited submits** — continue requiring explicit approval before any Kaggle upload.

---

## 7. Takeaways

- Raw LightGBM remains the workhorse; simple FE and pairwise interaction drips did not move OOF.
- Seed-bagging gave a small but real OOF lift (**+0.00013**); diversity from CatBoost did not.
- Two-slot Playground selection is being used as intended: single-seed + bag, private takes the max.

*Generated for the public `graphedge/playground-series-s6e9` repository. Redactions: no Kaggle submission refs, no competition handle/team name, no local filesystem paths.*
