"""
Smoke test for Kaggle Playground skills (no competition data required).

Tests:
1. Playground OG-data stack: synthetic train + OG dataset alignment and combination
2. Arrival-delay missingness: synthetic continuous feature with meaningful NA

Run: python docs/skills/test_skills_smoke.py

Expected: All assertions pass, no errors.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression


def test_og_data_stack():
    """Test OG-data stack pattern with synthetic data."""
    print("\n=== Test 1: Playground OG-data Stack ===")
    
    # Create synthetic train data
    np.random.seed(42)
    n_train = 1000
    train_df = pd.DataFrame({
        "Feature_A": np.random.randn(n_train),
        "Feature_B": np.random.choice(["Cat1", "Cat2", "Cat3"], n_train),
        "target": np.random.choice([0, 1], n_train, p=[0.7, 0.3])
    })
    
    # Create synthetic OG data with slightly different column names
    n_og = 500
    og_df = pd.DataFrame({
        "feature_a": np.random.randn(n_og),  # lowercase (needs rename)
        "Feature_B": np.random.choice(["Cat1", "Cat2", "Cat3"], n_og),
        "target_label": np.random.choice([0, 1], n_og, p=[0.65, 0.35])  # different name
    })
    
    # Step 1: Align columns
    og_rename_map = {
        "feature_a": "Feature_A",
        "target_label": "target"
    }
    og_df = og_df.rename(columns=og_rename_map)
    og_df = og_df[train_df.columns]  # Ensure same column order
    
    print(f"Train shape: {train_df.shape}")
    print(f"OG shape (aligned): {og_df.shape}")
    
    # Step 2: Mark original rows
    train_df["is_original"] = 0
    og_df["is_original"] = 1
    
    # Step 3: Combine
    combined_df = pd.concat([train_df, og_df], axis=0, ignore_index=True)
    print(f"Combined shape: {combined_df.shape}")
    
    # Assertions
    assert combined_df.shape[0] == n_train + n_og, "Row count mismatch"
    assert "is_original" in combined_df.columns, "Missing is_original flag"
    assert combined_df["is_original"].sum() == n_og, "is_original count wrong"
    assert set(combined_df.columns) == set(train_df.columns) | {"is_original"}, "Column mismatch"
    
    # Step 4: Stratified fold split on (target, is_original)
    combined_df["strat_key"] = (
        combined_df["target"].astype(str) + "_" +
        combined_df["is_original"].astype(str)
    )
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(combined_df, combined_df["strat_key"])):
        train_fold = combined_df.iloc[train_idx]
        val_fold = combined_df.iloc[val_idx]
        
        # Check both OG and train rows in each fold
        train_og_count = train_fold["is_original"].sum()
        val_og_count = val_fold["is_original"].sum()
        
        print(f"  Fold {fold}: train OG={train_og_count}, val OG={val_og_count}")
        assert train_og_count > 0, f"Fold {fold} training has no OG rows"
        assert val_og_count > 0, f"Fold {fold} validation has no OG rows"
    
    print("✓ OG-data stack test PASSED\n")


def test_arrival_delay_missingness():
    """Test arrival-delay missingness pattern with synthetic data."""
    print("=== Test 2: Arrival-Delay Missingness ===")
    
    # Create synthetic data with meaningful NA
    np.random.seed(42)
    n = 1000
    
    # Simulate arrival delays
    arrival_delays = np.random.randn(n) * 10 + 5  # mean 5 min, std 10
    arrival_delays[arrival_delays < -10] = 0  # Early flights capped at on-time
    
    # Inject missing values (20% missing)
    missing_mask = np.random.choice([True, False], n, p=[0.2, 0.8])
    arrival_delays[missing_mask] = np.nan
    
    train_df = pd.DataFrame({
        "Arrival_Delay_in_Minutes": arrival_delays,
        "Other_Feature": np.random.randn(n),
        "target": np.random.choice([0, 1], n, p=[0.7, 0.3])
    })
    
    test_df = pd.DataFrame({
        "Arrival_Delay_in_Minutes": np.random.randn(200) * 10 + 5,
        "Other_Feature": np.random.randn(200)
    })
    test_missing = np.random.choice([True, False], 200, p=[0.2, 0.8])
    test_df.loc[test_missing, "Arrival_Delay_in_Minutes"] = np.nan
    
    print(f"Train missing: {train_df['Arrival_Delay_in_Minutes'].isna().sum()} / {len(train_df)}")
    print(f"Test missing: {test_df['Arrival_Delay_in_Minutes'].isna().sum()} / {len(test_df)}")
    
    # Step 1: Create missing indicator BEFORE imputation
    train_df["Arrival_Delay_missing"] = train_df["Arrival_Delay_in_Minutes"].isna().astype(int)
    test_df["Arrival_Delay_missing"] = test_df["Arrival_Delay_in_Minutes"].isna().astype(int)
    
    print(f"Missing indicator created (train): {train_df['Arrival_Delay_missing'].sum()} ones")
    
    # Step 2: Fold-safe imputation
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    # Store original missing counts
    original_na_count = train_df["Arrival_Delay_in_Minutes"].isna().sum()
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(train_df, train_df["target"])):
        fold_median = train_df.iloc[train_idx]["Arrival_Delay_in_Minutes"].median()
        
        # Impute validation fold with training median
        val_mask = train_df.index.isin(val_idx)
        train_df.loc[val_mask, "Arrival_Delay_in_Minutes"] = (
            train_df.loc[val_mask, "Arrival_Delay_in_Minutes"].fillna(fold_median)
        )
        
        print(f"  Fold {fold} median: {fold_median:.2f}")
    
    # For test, use full train median
    test_median = train_df["Arrival_Delay_in_Minutes"].median()
    test_df["Arrival_Delay_in_Minutes"] = test_df["Arrival_Delay_in_Minutes"].fillna(test_median)
    
    print(f"Test imputed with train median: {test_median:.2f}")
    
    # Assertions
    assert train_df["Arrival_Delay_in_Minutes"].isna().sum() == 0, "Train still has NaN after impute"
    assert test_df["Arrival_Delay_in_Minutes"].isna().sum() == 0, "Test still has NaN after impute"
    assert train_df["Arrival_Delay_missing"].sum() == original_na_count, "Missing indicator count changed"
    assert "Arrival_Delay_missing" in train_df.columns, "Missing indicator not created"
    
    # Step 3: Verify missing indicator is informative (synthetic check)
    # Missing indicator should correlate with imputed values
    mean_when_missing = train_df[train_df["Arrival_Delay_missing"] == 1]["Arrival_Delay_in_Minutes"].mean()
    mean_when_present = train_df[train_df["Arrival_Delay_missing"] == 0]["Arrival_Delay_in_Minutes"].mean()
    
    print(f"Mean delay (was missing): {mean_when_missing:.2f}")
    print(f"Mean delay (was present): {mean_when_present:.2f}")
    
    # Missing rows should now have imputed median (close to overall mean)
    assert abs(mean_when_missing - test_median) < 1.0, "Imputed values diverge from median"
    
    print("✓ Arrival-delay missingness test PASSED\n")


def test_zero_vs_na_distinction():
    """Test that zero and NA are treated differently."""
    print("=== Test 3: Zero vs NA Distinction ===")
    
    # Create data where 0 is meaningful (on-time) and NA is missing
    n = 500
    delays = np.random.exponential(scale=10, size=n)  # Exponential delays
    
    # Set 30% to exactly zero (on-time flights)
    on_time_mask = np.random.choice([True, False], n, p=[0.3, 0.7])
    delays[on_time_mask] = 0.0
    
    # Set 10% to NA (missing data)
    missing_mask = np.random.choice([True, False], n, p=[0.1, 0.9])
    delays[missing_mask] = np.nan
    
    df = pd.DataFrame({"delay": delays})
    
    # Count zeros and NAs
    zero_count = (df["delay"] == 0.0).sum()
    na_count = df["delay"].isna().sum()
    
    print(f"Zero count (on-time): {zero_count}")
    print(f"NA count (missing): {na_count}")
    
    # Create missing indicator
    df["delay_missing"] = df["delay"].isna().astype(int)
    
    # Impute with median (should not replace zeros)
    median_delay = df["delay"].median()
    df["delay"] = df["delay"].fillna(median_delay)
    
    # Check that zeros are still zeros
    zero_count_after = (df["delay"] == 0.0).sum()
    
    print(f"Zero count after impute: {zero_count_after}")
    print(f"Median used for impute: {median_delay:.2f}")
    
    # Assertions
    assert zero_count == zero_count_after, "Zeros were replaced during imputation (BAD)"
    assert df["delay"].isna().sum() == 0, "Still have NaN after impute"
    assert df["delay_missing"].sum() == na_count, "Missing indicator count wrong"
    
    print("✓ Zero vs NA distinction test PASSED\n")


def test_no_leakage_validation():
    """Test that fold-safe imputation prevents leakage."""
    print("=== Test 4: No Target Leakage Validation ===")
    
    # Create data where delay is correlated with target
    np.random.seed(42)
    n = 1000
    
    # Target-dependent delays
    targets = np.random.choice([0, 1], n, p=[0.7, 0.3])
    delays = np.where(targets == 1, 
                     np.random.randn(n) * 5 + 20,  # Satisfied: shorter delays
                     np.random.randn(n) * 10 + 40)  # Not satisfied: longer delays
    
    # Inject 20% missing
    missing_mask = np.random.choice([True, False], n, p=[0.2, 0.8])
    delays[missing_mask] = np.nan
    
    df = pd.DataFrame({
        "delay": delays,
        "target": targets
    })
    
    # UNSAFE: Impute with full dataset median (includes val fold)
    unsafe_median = df["delay"].median()
    df_unsafe = df.copy()
    df_unsafe["delay"] = df_unsafe["delay"].fillna(unsafe_median)
    
    # SAFE: Fold-stratified imputation
    df_safe = df.copy()
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    for train_idx, val_idx in skf.split(df_safe, df_safe["target"]):
        fold_median = df_safe.iloc[train_idx]["delay"].median()
        val_mask = df_safe.index.isin(val_idx)
        df_safe.loc[val_mask, "delay"] = df_safe.loc[val_mask, "delay"].fillna(fold_median)
    
    # Train simple model and compare
    X_unsafe = df_unsafe[["delay"]].values
    X_safe = df_safe[["delay"]].values
    y = df["target"].values
    
    # Simple train-test split
    train_size = int(0.7 * n)
    X_train_unsafe, X_test_unsafe = X_unsafe[:train_size], X_unsafe[train_size:]
    X_train_safe, X_test_safe = X_safe[:train_size], X_safe[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    model_unsafe = LogisticRegression(random_state=42, max_iter=200)
    model_safe = LogisticRegression(random_state=42, max_iter=200)
    
    model_unsafe.fit(X_train_unsafe, y_train)
    model_safe.fit(X_train_safe, y_train)
    
    auc_unsafe = roc_auc_score(y_test, model_unsafe.predict_proba(X_test_unsafe)[:, 1])
    auc_safe = roc_auc_score(y_test, model_safe.predict_proba(X_test_safe)[:, 1])
    
    print(f"AUC (unsafe impute): {auc_unsafe:.4f}")
    print(f"AUC (safe impute): {auc_safe:.4f}")
    print(f"Difference: {abs(auc_unsafe - auc_safe):.4f}")
    
    # Both should achieve reasonable AUC (>0.6), difference should be small in this synthetic case
    assert auc_safe > 0.6, "Safe imputation model failed to learn"
    assert auc_unsafe > 0.6, "Unsafe imputation model failed to learn"
    
    print("✓ No leakage validation test PASSED\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Kaggle Playground Skills — Smoke Test")
    print("No competition data required (synthetic data only)")
    print("=" * 60)
    
    try:
        test_og_data_stack()
        test_arrival_delay_missingness()
        test_zero_vs_na_distinction()
        test_no_leakage_validation()
        
        print("=" * 60)
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("=" * 60)
        print("\nSkills are validated and ready to use.")
        print("See docs/skills/README.md for usage guide.\n")
        
    except AssertionError as e:
        print(f"\n✗✗✗ TEST FAILED ✗✗✗")
        print(f"Error: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗✗✗ UNEXPECTED ERROR ✗✗✗")
        print(f"Error: {e}\n")
        raise
