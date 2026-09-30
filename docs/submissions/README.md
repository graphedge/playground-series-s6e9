# EV Purchases — local submission artifacts (Spec 003)

## What this is

Local Kaggle-format submission CSV for the **raw LightGBM** 5-fold baseline
(the ~0.9416 OOF model on Spec 003).

**Upload is gated.** Do not run `kaggle competitions submit` (or any upload)
until Brett explicitly asks.

## Files

| File | Description |
|------|-------------|
| `submission_lgbm_raw_5fold.csv` | Columns `id,Will_Buy_EV`; probs in (0,1); row order matches `sample_submission.csv` |
| `submission_lgbm_raw_5fold_meta.json` | OOF AUC/PR-AUC, fold AUCs, params, `submitted_to_kaggle: false` |
| `README.md` | This note |

## Model

- LightGBM binary classifier, raw features (no engineered extras)
- Encoding: Subsidy No/Yes→0/1; Range_Anxiety Low/Med/High→0/1/2; other cats factorized (train+test together, sorted)
- StratifiedKFold 5, shuffle=True, random_state=42
- Per-fold `scale_pos_weight = n_neg/n_pos` on fold train; early stopping on fold valid
- Params: lr=0.05, n_estimators=500, max_depth=6, num_leaves=31, subsample/colsample=0.8, seed=42
- Test probs = mean of 5 fold `predict_proba`

## Script

`scripts/05_make_submission_raw_lgbm.py`

CSV data lives outside git (`data/` excluded in `.gitignore`).

Suggested Kaggle message when/if uploading: `lgbm raw 5fold`
