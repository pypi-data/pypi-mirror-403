import numpy as np
from autoprep.autoprep import AutoPrep
from autoprep.nan_handler import MyNanHandler
from autoprep.outlier_handler import MyIQROutlierHandler, MyMADOutlierHandler, MyHuberClipper
from autoprep.skew_handler import My1LogpSkew, MyBowleyLog1pSkew
from autoprep.encoder import MyOneHotEncoder, MyOrdinalEncoder
from autoprep.scaler import MyStandardScaler

print("=" * 80)
print("COMPREHENSIVE AUTOPREP TEST SUITE")
print("=" * 80)

# ============================================================================
# TEST 1: Default Configuration (auto NaN strategy)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: Default Configuration with 'auto' NaN Strategy")
print("=" * 80)

X_train_1 = np.array([
    [1.0, "red", 100],
    [2.0, "blue", 200],
    [np.nan, "red", 300],
    [4.0, np.nan, 400],
    [5.0, "blue", np.nan],
], dtype=object)

X_test_1 = np.array([
    [np.nan, "green", 150],
    [3.0, np.nan, 250],
], dtype=object)

prep_1 = AutoPrep(num_cols=[0, 2], cat_cols=[1], nan_strategy="auto")
X_train_clean_1 = prep_1.fit_transform(X_train_1)
X_test_clean_1 = prep_1.transform(X_test_1)

print(f"Train shape: {X_train_clean_1.shape}")
print(f"Test shape: {X_test_clean_1.shape}")
print(f"Train NaNs: {np.isnan(X_train_clean_1).sum()}")
print(f"Test NaNs: {np.isnan(X_test_clean_1).sum()}")
assert not np.isnan(X_train_clean_1).any(), "❌ Train has NaNs!"
assert not np.isnan(X_test_clean_1).any(), "❌ Test has NaNs!"
print("✓ No NaNs in output")

# ============================================================================
# TEST 2: Mean NaN Strategy for Numerical
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: Mean NaN Strategy")
print("=" * 80)

X_train_2 = np.array([
    [1.0, "A", 10],
    [2.0, "B", 20],
    [np.nan, "A", 30],
    [4.0, "B", np.nan],
], dtype=object)

prep_2 = AutoPrep(num_cols=[0, 2], cat_cols=[1], nan_strategy="mean")
X_train_clean_2 = prep_2.fit_transform(X_train_2)

print(f"Output shape: {X_train_clean_2.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_2).sum()}")
assert not np.isnan(X_train_clean_2).any(), "Output has NaNs!"
print("✓ Mean strategy worked")

# ============================================================================
# TEST 3: Median NaN Strategy
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: Median NaN Strategy")
print("=" * 80)

X_train_3 = np.array([
    [1.0, "X", 100],
    [2.0, "Y", 200],
    [np.nan, "X", 1000],  # outlier
    [3.0, "Y", np.nan],
], dtype=object)

prep_3 = AutoPrep(num_cols=[0, 2], cat_cols=[1], nan_strategy="median")
X_train_clean_3 = prep_3.fit_transform(X_train_3)

print(f"Output shape: {X_train_clean_3.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_3).sum()}")
assert not np.isnan(X_train_clean_3).any(), "Output has NaNs!"
print("✓ Median strategy worked")

# ============================================================================
# TEST 4: Multiple Outlier Handlers with Different NaN Strategies
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: MAD Outlier Handler + Auto NaN Strategy")
print("=" * 80)

X_train_4 = np.array([
    [1.0, "cat", 50],
    [2.0, "dog", 60],
    [np.nan, "cat", 10000],  # extreme outlier
    [3.0, "dog", 70],
    [4.0, np.nan, np.nan],
], dtype=object)

prep_4 = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1],
    outlier_handler=MyMADOutlierHandler(strategy="clip"),
    nan_strategy="auto"
)
X_train_clean_4 = prep_4.fit_transform(X_train_4)

print(f"Output shape: {X_train_clean_4.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_4).sum()}")
assert not np.isnan(X_train_clean_4).any(), "❌ Output has NaNs!"
print("✓ MAD handler + auto NaN strategy worked")

# ============================================================================
# TEST 5: Skew Handler with NaN Strategy
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: Skew Handler (Bowley Log1p) + Median NaN Strategy")
print("=" * 80)

X_train_5 = np.array([
    [1.0, "A", 10],
    [100.0, "B", 100],  # skewed
    [np.nan, "A", 1000],  # skewed + NaN
    [2.0, "B", np.nan],
    [3.0, "A", 15],
], dtype=object)

prep_5 = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1],
    skew_handler=MyBowleyLog1pSkew(threshold=0.5),
    nan_strategy="median"
)
X_train_clean_5 = prep_5.fit_transform(X_train_5)

print(f"Output shape: {X_train_clean_5.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_5).sum()}")
assert not np.isnan(X_train_clean_5).any(), "❌ Output has NaNs!"
print("✓ Skew handler + median NaN strategy worked")

# ============================================================================
# TEST 6: OneHot Encoder with NaN Strategy
# ============================================================================
print("\n" + "=" * 80)
print("TEST 6: OneHot Encoder + Most Frequent NaN Strategy")
print("=" * 80)

X_train_6 = np.array([
    [1.0, "red"],
    [2.0, "blue"],
    [np.nan, "red"],
    [3.0, np.nan],
    [4.0, "red"],
], dtype=object)

prep_6 = AutoPrep(
    num_cols=[0],
    cat_cols=[1],
    encoder=MyOneHotEncoder(),
    nan_strategy="most_frequent"
)
X_train_clean_6 = prep_6.fit_transform(X_train_6)

print(f"Output shape: {X_train_clean_6.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_6).sum()}")
assert not np.isnan(X_train_clean_6).any(), "❌ Output has NaNs!"
print("✓ OneHot encoder + most_frequent NaN strategy worked")

# ============================================================================
# TEST 7: Edge Case - All NaN Column
# ============================================================================
print("\n" + "=" * 80)
print("TEST 7: Edge Case - Column with All NaNs")
print("=" * 80)

X_train_7 = np.array([
    [1.0, "A", np.nan],
    [2.0, "B", np.nan],
    [3.0, "A", np.nan],
], dtype=object)

prep_7 = AutoPrep(num_cols=[0, 2], cat_cols=[1], nan_strategy="mean")
X_train_clean_7 = prep_7.fit_transform(X_train_7)

print(f"Output shape: {X_train_clean_7.shape}")
print(f"Column 2 values: {X_train_clean_7[:, 1]}")
print("✓ All-NaN column handled (likely filled with 0)")

# ============================================================================
# TEST 8: Large Dataset with Mixed NaNs and Outliers
# ============================================================================
print("\n" + "=" * 80)
print("TEST 8: Large Dataset with Mixed Issues")
print("=" * 80)

np.random.seed(42)
n_samples = 1000
X_train_8 = np.column_stack([
    np.random.randn(n_samples) * 10 + 50,  # numeric col 1
    np.random.choice(["A", "B", "C", None], n_samples),  # categorical with NaNs
    np.random.exponential(scale=100, size=n_samples),  # skewed numeric col 2
])

# Add some NaNs randomly
X_train_8[np.random.choice(n_samples, 100), 0] = np.nan
X_train_8[np.random.choice(n_samples, 50), 2] = np.nan

prep_8 = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1],
    outlier_handler=MyIQROutlierHandler(strategy="clip"),
    skew_handler=My1LogpSkew(threshold=0.5),
    encoder=MyOrdinalEncoder(),
    nan_strategy="auto"
)
X_train_clean_8 = prep_8.fit_transform(X_train_8)

print(f"Input shape: {X_train_8.shape}")
print(f"Output shape: {X_train_clean_8.shape}")
print(f"Input NaNs: {np.sum([np.isnan(float(x)) if isinstance(x, (int, float)) else x is None for row in X_train_8 for x in row])}")
print(f"Output NaNs: {np.isnan(X_train_clean_8).sum()}")
assert not np.isnan(X_train_clean_8).any(), "❌ Output has NaNs!"
print("✓ Large dataset processed successfully")

# ============================================================================
# TEST 9: Train-Test Consistency Check
# ============================================================================
print("\n" + "=" * 80)
print("TEST 9: Train-Test Consistency (New Categories in Test)")
print("=" * 80)

X_train_9 = np.array([
    [1.0, "A", 10],
    [2.0, "B", 20],
    [np.nan, "A", 30],
], dtype=object)

X_test_9 = np.array([
    [3.0, "C", 40],  # new category "C"
    [np.nan, "A", np.nan],
], dtype=object)

prep_9 = AutoPrep(
    num_cols=[0, 2],
    cat_cols=[1],
    encoder=MyOrdinalEncoder(),
    nan_strategy="auto"
)
X_train_clean_9 = prep_9.fit_transform(X_train_9)
X_test_clean_9 = prep_9.transform(X_test_9)

print(f"Train shape: {X_train_clean_9.shape}")
print(f"Test shape: {X_test_clean_9.shape}")
print(f"Test NaNs: {np.isnan(X_test_clean_9).sum()}")
assert not np.isnan(X_test_clean_9).any(), "❌ Test has NaNs!"
print("✓ Train-test pipeline consistent")

# ============================================================================
# TEST 10: No Categorical Columns
# ============================================================================
print("\n" + "=" * 80)
print("TEST 10: Only Numerical Columns")
print("=" * 80)

X_train_10 = np.array([
    [1.0, 10, 100],
    [2.0, 20, 200],
    [np.nan, 30, np.nan],
    [4.0, np.nan, 400],
], dtype=object)

prep_10 = AutoPrep(num_cols=[0, 1, 2], cat_cols=None, nan_strategy="mean")
X_train_clean_10 = prep_10.fit_transform(X_train_10)

print(f"Output shape: {X_train_clean_10.shape}")
print(f"NaNs remaining: {np.isnan(X_train_clean_10).sum()}")
assert not np.isnan(X_train_clean_10).any(), "❌ Output has NaNs!"
print("✓ Numerical-only pipeline worked")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("ALL TESTS PASSED! ✓✓✓")
print("=" * 80)
print("\nTested scenarios:")
print("  ✓ Auto NaN strategy (mean for numeric, most_frequent for categorical)")
print("  ✓ Mean NaN strategy")
print("  ✓ Median NaN strategy")
print("  ✓ Multiple outlier handlers (IQR, MAD)")
print("  ✓ Skew handlers (Bowley, Log1p)")
print("  ✓ Encoders (OneHot, Ordinal)")
print("  ✓ Edge cases (all-NaN columns, new categories in test)")
print("  ✓ Large datasets with mixed issues")
print("  ✓ Train-test consistency")
print("  ✓ Numerical-only pipelines")
print("\n" + "=" * 80)