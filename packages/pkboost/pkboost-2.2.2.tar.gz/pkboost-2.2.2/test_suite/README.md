# PKBoost Test Suite

## Overview

This directory contains a comprehensive test suite for PKBoost, including:
- A benchmark script using direct ndarray types (no Vec conversion)
- Unit tests for core functionality
- Edge case tests
- Integration tests

## Files

### Benchmark
- **`benchmark_ndarray.rs`** - Benchmark script that loads CSV directly into `ndarray::Array2` and `Array1`, then uses `.view()` to get `ArrayView2`/`ArrayView1` for the API. This is the **direct ndarray version** you requested.

### Test Files
- **`test_model_training.rs`** - Tests model training on balanced/imbalanced data, validation sets, missing values, etc.
- **`test_edge_cases.rs`** - Tests edge cases: empty data, single samples, all same class, dimension mismatches, etc.
- **`test_multiclass.rs`** - Tests multi-class classification functionality
- **`test_regression.rs`** - Tests regression functionality
- **`test_integration.rs`** - Full workflow tests including serialization

### Helper Module
- **`test_helpers.rs`** - Common utilities for generating synthetic test data

## Key Difference: Direct ndarray Usage

The `benchmark_ndarray.rs` file demonstrates the **correct way** to use PKBoost:

```rust
// Load CSV directly into Array2/Array1
let (x_train, y_train) = load_csv_to_ndarray("data/train.csv")?;

// Use .view() to get ArrayView2/ArrayView1 - NO CONVERSION NEEDED!
let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
model.fit(x_train.view(), y_train.view(), Some((x_val.view(), y_val.view())), true)?;
let predictions = model.predict_proba(x_test.view())?;
```

**No Vec conversion needed!** The API is designed to work with `ndarray` types directly.

## Running

### Run Benchmark:
```bash
cargo run --bin benchmark_ndarray --release
```

### Run All Tests:
```bash
# These will be run as integration tests
cargo test --test test_model_training
cargo test --test test_edge_cases  
cargo test --test test_multiclass
cargo test --test test_regression
cargo test --test test_integration
```

### Run Specific Test:
```bash
cargo test --test test_model_training test_model_trains_on_balanced_data
```

## Test Coverage

### ✅ Model Training (6 tests)
- Balanced data training
- Imbalanced data (1% positive)
- Validation set usage
- Missing value handling
- Prediction consistency
- Auto-tuning validation

### ✅ Edge Cases (9 tests)
- Empty datasets
- Single samples
- All same class
- Single feature
- Large datasets
- Dimension mismatches
- All-NaN features
- Unfitted model errors
- Wrong prediction dimensions

### ✅ Multi-Class (4 tests)
- Multi-class training
- Probability validation
- Accuracy calculation
- Imbalanced multi-class

### ✅ Regression (5 tests)
- Regression training
- RMSE/R² calculation
- Validation sets
- Outlier handling
- MAE calculation

### ✅ Integration (4 tests)
- Full workflow
- Serialization
- Feature usage
- Early stopping

**Total: 28 comprehensive tests**

## What Was Missing

The original codebase had:
- ❌ Only 6 small unit tests (tree, loss functions)
- ❌ No integration tests
- ❌ No edge case tests
- ❌ No multi-class tests
- ❌ No regression tests
- ❌ No model training tests

This test suite fills all those gaps!

## Notes

- All tests use synthetic data for reproducibility
- Tests run quickly (< 1 second each)
- Tests verify both success and error cases
- Benchmark uses real CSV data (requires `data/` directory)
