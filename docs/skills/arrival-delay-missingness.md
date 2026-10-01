---
skill_type: kaggle_playground
domain: feature_engineering
applies_to: continuous_features_with_meaningful_na
---

# Arrival-Delay / Sparse Continuous Missingness — Feature Engineering

## When to Use This Skill

Use this skill when working with **continuous operational features** where `NaN` (missing) has **semantic meaning** distinct from zero.

**Canonical example**: `Arrival Delay in Minutes` from Kaggle Playground S6E10 Airline Satisfaction
- `NaN` = flight data not recorded (system issue, missing sensor, cancelled flight)
- `0.0` = on-time arrival (no delay)
- `> 0` = minutes late
- `< 0` = arrived early

**Other applicable domains**:
- Manufacturing: sensor downtime (`NaN`) vs working but idle (`0.0`)
- Healthcare: test not ordered (`NaN`) vs normal result (`0.0`)
- Finance: transaction not attempted (`NaN`) vs $0 transaction
- Logistics: delivery time not tracked vs delivered instantly

**Signal to trigger**: Feature has >5% `NaN` values AND zero is a valid, frequent value (not used as a missing-value sentinel).

## Skill Overview

The arrival-delay missingness workflow:
1. **Create missing indicator** (`_missing` binary flag)
2. **Impute safely** (median or fold-stratified, no target leakage)
3. **Optional: Compute delay gap** (arrival delay − departure delay when both present)
4. **Validate** no zero-vs-NA conflation or leakage

Expected lift: +0.001 to +0.005 AUC when missingness is informative.

## Step-by-Step Execution

### Step 0: Diagnose the Feature

```python
import pandas as pd
import numpy as np

train_df = pd.read_csv("data/train.csv")
feature = "Arrival_Delay_in_Minutes"

# Inspect missingness and distribution
print(f"Missing: {train_df[feature].isna().sum()} / {len(train_df)} "
      f"({100 * train_df[feature].isna().mean():.1f}%)")
print(f"Zero count: {(train_df[feature] == 0.0).sum()}")
print(f"Negative count: {(train_df[feature] < 0).sum()}")
print(f"\nDistribution (non-missing):")
print(train_df[feature].describe())

# Check if missingness correlates with target
if "Satisfaction" in train_df.columns:
    missing_mask = train_df[feature].isna()
    target_rate_missing = train_df.loc[missing_mask, "Satisfaction"].mean()
    target_rate_present = train_df.loc[~missing_mask, "Satisfaction"].mean()
    print(f"\nTarget rate (missing): {target_rate_missing:.3f}")
    print(f"Target rate (present): {target_rate_present:.3f}")
    print(f"Delta: {abs(target_rate_missing - target_rate_present):.3f}")
```

**Decision rules**:
- Delta > 0.02 → Missing indicator is likely informative
- Delta < 0.005 → Missing indicator may not help
- Zero count > 10% → Zero is semantically distinct from NA (proceed with this skill)

### Step 1: Create Missing Indicator

```python
# Create binary flag BEFORE imputation
train_df["Arrival_Delay_missing"] = train_df["Arrival_Delay_in_Minutes"].isna().astype(int)

# Apply same logic to test
test_df["Arrival_Delay_missing"] = test_df["Arrival_Delay_in_Minutes"].isna().astype(int)

print(f"Missing indicator created. Value counts:")
print(train_df["Arrival_Delay_missing"].value_counts())
```

**Why first**: Once you impute, you lose the ability to distinguish `NaN` from filled values. The missing indicator preserves this signal.

### Step 2: Impute Safely (No Target Leakage)

**Option A: Global median (simplest, weak)**

```python
# Compute median from TRAIN only
median_delay = train_df["Arrival_Delay_in_Minutes"].median()

train_df["Arrival_Delay_in_Minutes"] = train_df["Arrival_Delay_in_Minutes"].fillna(median_delay)
test_df["Arrival_Delay_in_Minutes"] = test_df["Arrival_Delay_in_Minutes"].fillna(median_delay)
```

**Option B: Fold-stratified median (safer for CV)**

```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, val_idx) in enumerate(skf.split(train_df, train_df["Satisfaction"])):
    # Compute median from training fold only
    fold_median = train_df.iloc[train_idx]["Arrival_Delay_in_Minutes"].median()
    
    # Impute validation fold with training median
    val_mask = train_df.index.isin(val_idx)
    train_df.loc[val_mask, "Arrival_Delay_in_Minutes"] = (
        train_df.loc[val_mask, "Arrival_Delay_in_Minutes"].fillna(fold_median)
    )

# For test, use full train median
test_median = train_df["Arrival_Delay_in_Minutes"].median()
test_df["Arrival_Delay_in_Minutes"] = test_df["Arrival_Delay_in_Minutes"].fillna(test_median)
```

**Option C: Group-based imputation (advanced)**

```python
# Impute by categorical group (e.g., Class or Type_of_Travel)
train_df["Arrival_Delay_in_Minutes"] = train_df.groupby("Class")["Arrival_Delay_in_Minutes"].transform(
    lambda x: x.fillna(x.median())
)
# Handle any remaining NaNs with global median
train_df["Arrival_Delay_in_Minutes"] = train_df["Arrival_Delay_in_Minutes"].fillna(
    train_df["Arrival_Delay_in_Minutes"].median()
)
```

**Unsafe pattern**: Using full train+val target to compute imputation statistics before splitting.

### Step 3 (Optional): Compute Delay Gap

If **both** `Departure_Delay_in_Minutes` and `Arrival_Delay_in_Minutes` are present:

```python
# Only compute gap where both are non-missing (pre-imputation check)
delay_gap_mask = (
    train_df["Departure_Delay_in_Minutes"].notna() &
    train_df["Arrival_Delay_in_Minutes"].notna()
)

train_df["Delay_Gap"] = np.nan
train_df.loc[delay_gap_mask, "Delay_Gap"] = (
    train_df.loc[delay_gap_mask, "Arrival_Delay_in_Minutes"] -
    train_df.loc[delay_gap_mask, "Departure_Delay_in_Minutes"]
)

# Fill remaining NaNs with 0 or median
train_df["Delay_Gap"] = train_df["Delay_Gap"].fillna(0.0)
```

**Interpretation**:
- Positive gap: Flight made up time in the air (good operations signal)
- Negative gap: Flight lost time in the air (weather, congestion)
- `NaN` → 0: No information (conservative)

**When to use**: Delay gap may help models learn operational efficiency patterns.

### Step 4: Validate No Leakage or Conflation

**Checklist**:
- [ ] Missing indicator created BEFORE imputation
- [ ] Imputation uses train-only statistics (not train+val)
- [ ] Test set uses train's imputation fill value (not test's own median)
- [ ] Zero values are preserved (not replaced with median)
- [ ] No target-derived imputation (e.g., filling `NaN` with mean delay of satisfied customers)

**Common mistake**: Treating `0.0` as "missing" and replacing it with median.

```python
# BAD: This destroys the meaning of zero (on-time arrival)
train_df["Arrival_Delay_in_Minutes"] = train_df["Arrival_Delay_in_Minutes"].replace(0, np.nan).fillna(median)

# GOOD: Only fill actual NaN, leave 0.0 intact
train_df["Arrival_Delay_in_Minutes"] = train_df["Arrival_Delay_in_Minutes"].fillna(median)
```

### Step 5: Feature Interaction with Missing Indicator

The missing indicator can interact with other features:

```python
# Example: Class × missing indicator (business class flights may have better tracking)
train_df["Class_x_Delay_Missing"] = (
    train_df["Class"].astype(str) + "_" +
    train_df["Arrival_Delay_missing"].astype(str)
)

# Or polynomial feature
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
poly_features = poly.fit_transform(train_df[["Arrival_Delay_in_Minutes", "Arrival_Delay_missing"]])
```

**Use sparingly**: Only test interactions if baseline missing indicator alone shows lift.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Zero treated as missing** | On-time flights coded as `NaN` | Only fill actual `NaN`, preserve `0.0` |
| **Imputation before split** | CV score +0.05, LB drops | Compute impute stats from train fold only |
| **Global mean instead of median** | Outliers (300min delay) skew fill value | Use median or percentile-based imputation |
| **Missing indicator omitted** | Model can't distinguish `NaN` vs imputed | Always create `_missing` flag first |
| **Target leakage in imputation** | Filling with satisfied customer avg delay | Only use feature-based or global stats |
| **Test imputed with test stats** | Test median != train median → shift | Use train's imputation value for test |

## Generalization to Other Features

This skill applies beyond arrival delay:

| Feature | NaN meaning | Zero meaning | Approach |
|---------|-------------|--------------|----------|
| `Sensor_Temperature` | Sensor offline | Freezing (0°C) | Missing indicator + median impute |
| `Transaction_Amount` | No transaction | $0 purchase | Missing indicator + 0 or median |
| `Test_Score` | Test not taken | Zero score (failed) | Missing indicator + group median |
| `Delivery_Days` | Not shipped yet | Same-day delivery | Missing indicator + forward-fill or median |

**Core principle**: If `NaN` and `0` have different real-world causes, treat them differently.

## Likert Scale Caveat (Negative Example)

**Do NOT apply this skill to Likert scales** where `0` is a response category (e.g., "Not at all satisfied" = 0).

```python
# BAD: Treating Likert 0 as missing
survey_df["Cleanliness_Score"].fillna(0)  # This is CORRECT for surveys

# BAD: Creating missing indicator for Likert
survey_df["Cleanliness_missing"] = survey_df["Cleanliness_Score"].isna()  # Only if truly missing
```

**Likert rule**: If the competition data dictionary says `0` is a valid response (e.g., 0-5 scale), then `NaN` is probably data entry error or optional question. Impute with mode or category-specific logic.

## Expected Outcomes

**Typical gains**:
- **+0.001 to +0.003 AUC**: Missing indicator alone (missingness is mildly informative)
- **+0.002 to +0.005 AUC**: Missing indicator + fold-safe median impute (replaces naive zero-fill)
- **+0.000 to +0.002 AUC**: Delay gap feature (weak signal unless operational efficiency matters)

**When to skip**:
- Missing rate <1% (insufficient signal)
- Zero and `NaN` mean the same thing (e.g., count data where 0 = none)
- Competition uses placeholder values (`-999` instead of `NaN`)

## Validation Checklist

Before final submission:
- [ ] Missing indicator created before imputation
- [ ] Imputation uses train-only statistics (fold-stratified if possible)
- [ ] Test set uses train's imputation value
- [ ] Zero values are preserved (not replaced)
- [ ] No target leakage in imputation logic
- [ ] CV score improvement validated on holdout fold
- [ ] Feature distributions before/after imputation are sensible (no wild outliers)

## Code Template (Full Pipeline)

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold

def engineer_sparse_continuous_feature(
    train_df, test_df, feature_name, strategy="median", fold_safe=True
):
    """
    Engineer a continuous feature with meaningful missingness.
    
    Args:
        train_df: Training dataframe
        test_df: Test dataframe
        feature_name: Column name (e.g., "Arrival_Delay_in_Minutes")
        strategy: "median" or "mean"
        fold_safe: If True, use fold-stratified imputation (requires target column)
    
    Returns:
        train_df, test_df with missing indicator and imputed feature
    """
    missing_col = f"{feature_name}_missing"
    
    # Step 1: Create missing indicator
    train_df[missing_col] = train_df[feature_name].isna().astype(int)
    test_df[missing_col] = test_df[feature_name].isna().astype(int)
    
    # Step 2: Impute
    if fold_safe and "target" in train_df.columns:
        # Fold-stratified imputation (safer for CV)
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        for train_idx, val_idx in skf.split(train_df, train_df["target"]):
            if strategy == "median":
                fill_value = train_df.iloc[train_idx][feature_name].median()
            else:
                fill_value = train_df.iloc[train_idx][feature_name].mean()
            
            train_df.loc[train_df.index[val_idx], feature_name] = (
                train_df.loc[train_df.index[val_idx], feature_name].fillna(fill_value)
            )
    else:
        # Global imputation
        if strategy == "median":
            fill_value = train_df[feature_name].median()
        else:
            fill_value = train_df[feature_name].mean()
        train_df[feature_name] = train_df[feature_name].fillna(fill_value)
    
    # Test uses train's fill value
    if strategy == "median":
        test_fill = train_df[feature_name].median()
    else:
        test_fill = train_df[feature_name].mean()
    test_df[feature_name] = test_df[feature_name].fillna(test_fill)
    
    return train_df, test_df


# Usage
train, test = engineer_sparse_continuous_feature(
    train_df, test_df, 
    "Arrival_Delay_in_Minutes", 
    strategy="median", 
    fold_safe=True
)
```

## References

- Missing data patterns: https://www.kaggle.com/code/alexisbcook/missing-values
- Imputation strategies: https://scikit-learn.org/stable/modules/impute.html
- S6E10 Airline Satisfaction (canonical arrival delay example)

## Related Skills

- `playground-og-data-stack.md` — Handle original dataset integration (may also have NA patterns)
- `scripts/03_baselines.py` — Standard 5-fold CV baseline pattern (extend with missingness handling)

---

**Status**: Active  
**Owner**: EV/playground-series-s6e9 (reusable across Playground and tabular competitions)  
**Last Updated**: 2026-10-01
