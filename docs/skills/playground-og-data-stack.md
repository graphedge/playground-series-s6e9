---
skill_type: kaggle_playground
domain: tabular_data
applies_to: playground_series
---

# Playground OG-data Stack — Original Dataset Integration

## When to Use This Skill

Use this skill for **Kaggle Playground Series tabular competitions** where an "original" or parent public dataset exists that aligns with the competition train/test data.

**Examples**:
- S6E10 Airline Satisfaction: parent dataset from Invistico/TJ Klein (teejmahal20) on Kaggle
- S6E9 (hypothetical): if an original EV survey dataset existed
- Any Playground competition with acknowledged source data

**Signal to trigger**: Competition description mentions "synthetic data based on [Dataset Name]" or community identifies an aligned public dataset with similar schema and target.

## Skill Overview

The OG-data stack workflow:
1. **Align** the original dataset columns to match competition train schema
2. **Mark** OG rows with `is_original=1` flag
3. **Combine** OG rows with competition train (vertical stack)
4. **Train** models with expanded data and/or build secondary models on OG only
5. **Blend** OOF predictions or test probabilities across models
6. **Validate** no leakage rules are violated

Expected lift: +0.001 to +0.01 AUC depending on OG size, quality, and distribution shift.

## Step-by-Step Execution

### Step 1: Download and Inspect Original Dataset

```python
# Manual: Download from Kaggle Datasets UI or kaggle CLI
# kaggle datasets download -d <username>/<dataset-name>

import pandas as pd

og_df = pd.read_csv("data/original_dataset.csv")
train_df = pd.read_csv("data/train.csv")

print("OG shape:", og_df.shape)
print("Train shape:", train_df.shape)
print("\nOG columns:", sorted(og_df.columns))
print("Train columns:", sorted(train_df.columns))
```

**Checklist**:
- [ ] Column names approximately match (case, underscores, abbreviations)
- [ ] Target column exists in OG (may be different name: `satisfaction` vs `Satisfaction`)
- [ ] Feature dtypes compatible (numeric, categorical levels)
- [ ] No obvious distribution shift warnings (year ranges, category sets)

### Step 2: Align Columns to Train Schema

**Goal**: Rename OG columns to exactly match `train.csv` schema.

```python
# Example: S6E10 airline dataset
og_rename_map = {
    "satisfaction": "Satisfaction",  # target
    "Customer Type": "Customer_Type",
    "Age": "Age",
    "Type of Travel": "Type_of_Travel",
    "Class": "Class",
    # ... map all features
}

og_df = og_df.rename(columns=og_rename_map)

# Verify alignment
missing_in_og = set(train_df.columns) - set(og_df.columns)
extra_in_og = set(og_df.columns) - set(train_df.columns)

print(f"Missing in OG: {missing_in_og}")
print(f"Extra in OG: {extra_in_og}")

# Drop extra columns, add missing with NaN (rare)
og_df = og_df[train_df.columns]
```

**Pitfalls**:
- Target label encoding: OG may use `satisfied`/`neutral or dissatisfied` (strings) while train uses `1`/`0` (int)
  - **Fix**: Map strings to match train target encoding before stacking
- Feature values: OG `Class` = `Eco`, train = `Economy`
  - **Fix**: Recode OG categorical levels to match train

### Step 3: Mark Original Rows

```python
train_df["is_original"] = 0
og_df["is_original"] = 1

# Combine
combined_df = pd.concat([train_df, og_df], axis=0, ignore_index=True)
print("Combined shape:", combined_df.shape)
```

**Why**: The `is_original` flag lets you:
- Use it as a feature (weak signal of distribution shift)
- Train separate models on train-only vs OG-only subsets
- Stratify folds to ensure each fold has both sources

### Step 4: Prevent Target Leakage

**Critical leakage rules**:
1. **Never peek at competition test labels**: OG dataset must not contain test set ground truth
2. **Fold splits must respect `is_original`**: Use stratified folds on `(target, is_original)` or group-based splits
3. **No target-derived features from OG before split**: If creating target encodings, only use train portion

```python
from sklearn.model_selection import StratifiedKFold

# Safe: Stratify on target AND is_original
combined_df["strat_key"] = (
    combined_df["Satisfaction"].astype(str) + "_" +
    combined_df["is_original"].astype(str)
)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for fold, (train_idx, val_idx) in enumerate(skf.split(combined_df, combined_df["strat_key"])):
    # Ensure both OG and train rows in each fold
    pass
```

**Unsafe patterns**:
- Using OG target to impute missing values in train
- Creating target encodings across combined data before CV split
- Leaking test fold information into fold assignment

### Step 5: Training Strategies

**Option A: Single model on combined data**

```python
# LightGBM with sample_weight to balance train vs OG
train_weights = np.where(combined_df["is_original"] == 1, 
                         0.5,  # downweight OG if noisy
                         1.0)

lgb_params = {
    "objective": "binary",
    "metric": "auc",
    "verbosity": -1,
}

# Train with sample_weight in fit() or lgb.Dataset
```

**Option B: Two models + blend**

```python
# Model 1: Train on competition train only
model_train_only = train_lgb(train_df[train_df["is_original"] == 0])

# Model 2: Train on OG only (or combined)
model_og = train_lgb(og_df)

# Blend OOF predictions
oof_blend = 0.7 * oof_train_only + 0.3 * oof_og
test_blend = 0.7 * pred_test_train_only + 0.3 * pred_test_og
```

**Option C: Stacking meta-learner**

```python
# Use (oof_train_only, oof_og, is_original) as meta-features
meta_features = np.column_stack([oof_train_only, oof_og, combined_df["is_original"]])
meta_model = LogisticRegression().fit(meta_features, combined_df["Satisfaction"])
```

### Step 6: Validate No Double-Counting

**Pitfall**: If OG dataset overlaps with competition train (same passenger IDs), you'll double-count rows.

```python
# Check for ID overlap (if ID column exists)
if "id" in train_df.columns and "id" in og_df.columns:
    overlap = set(train_df["id"]) & set(og_df["id"])
    print(f"Overlapping IDs: {len(overlap)}")
    if overlap:
        print("WARNING: Drop duplicates or deduplicate before stacking")
        og_df = og_df[~og_df["id"].isin(train_df["id"])]
```

**Safe assumption**: Most Playground datasets are synthetic and have no ID overlap, but verify.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Target encoding mismatch** | OG uses `Yes/No`, train uses `1/0` | Map OG target to numeric before stack |
| **Column name case mismatch** | `KeyError` when selecting features | Use exact train column names (case-sensitive) |
| **Distribution shift ignored** | OG data is from 2015, train is 2023 | Add `year` or `data_source` feature; downweight OG |
| **Leakage in fold splits** | CV score jumps +0.05, LB drops | Stratify on `(target, is_original)` or use GroupKFold |
| **ID duplication** | Training set size inflated, overfitting | Drop OG rows with IDs in train |
| **Treating 0 vs NA the same** | OG has `NaN` delays, train has `0.0` | See companion skill: `arrival-delay-missingness.md` |

## Expected Outcomes

**Typical gains**:
- **+0.001 to +0.005 AUC**: OG data is high-quality and similar distribution
- **+0.005 to +0.01 AUC**: OG is large (>10k rows) and model learns broader patterns
- **No gain or negative**: OG is noisy, outdated, or distribution shift dominates

**When to skip**:
- OG dataset is <500 rows (noise > signal)
- OG target distribution is inverted (e.g., 90% positive vs 20% in train)
- Competition rules prohibit external data (rare for Playground)

## Validation Checklist

Before final submission:
- [ ] OG columns exactly match train schema (names, dtypes)
- [ ] Target encoding is aligned (numeric if train is numeric)
- [ ] `is_original` flag is present and correct
- [ ] Fold splits stratify on `(target, is_original)` or use safe GroupKFold
- [ ] No test set labels leaked from OG into train
- [ ] No ID duplication between OG and train
- [ ] CV score improvement is validated on holdout fold
- [ ] Test predictions are blended with appropriate weights (if using multiple models)

## References

- Kaggle Playground Series: https://www.kaggle.com/competitions?hostSegmentIdFilter=8
- Example: S6E10 Airline Satisfaction (Invistico dataset integration pattern)
- Leakage prevention: https://www.kaggle.com/code/alexisbcook/data-leakage

## Related Skills

- `arrival-delay-missingness.md` — Handle continuous features with meaningful NA
- `scripts/03_baselines.py` — Standard 5-fold CV baseline pattern (extend for OG stack)

---

**Status**: Active  
**Owner**: EV/playground-series-s6e9 (reusable across Playground competitions)  
**Last Updated**: 2026-10-01
