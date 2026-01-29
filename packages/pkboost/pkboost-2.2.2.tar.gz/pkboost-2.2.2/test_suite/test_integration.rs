//! Integration tests - full workflow tests

use pkboost::*;
use ndarray::{Array1, Array2};
use std::fs;

#[test]
fn test_full_classification_workflow() {
    // Create synthetic dataset
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let n_train = 1000;
    let n_test = 200;
    let n_features = 10;
    
    let mut x_train = Array2::zeros((n_train, n_features));
    let mut y_train = Array1::zeros(n_train);
    let mut x_test = Array2::zeros((n_test, n_features));
    let mut y_test = Array1::zeros(n_test);
    
    // Generate training data
    for i in 0..n_train {
        let is_positive = i < n_train / 10; // 10% positive
        for j in 0..n_features {
            if is_positive && j == 0 {
                x_train[[i, j]] = rng.gen_range(0.5..1.5);
            } else if !is_positive && j == 0 {
                x_train[[i, j]] = rng.gen_range(-1.5..0.5);
            } else {
                x_train[[i, j]] = rng.gen_range(-1.0..1.0);
            }
        }
        y_train[i] = if is_positive { 1.0 } else { 0.0 };
    }
    
    // Generate test data
    for i in 0..n_test {
        let is_positive = i < n_test / 10;
        for j in 0..n_features {
            if is_positive && j == 0 {
                x_test[[i, j]] = rng.gen_range(0.5..1.5);
            } else if !is_positive && j == 0 {
                x_test[[i, j]] = rng.gen_range(-1.5..0.5);
            } else {
                x_test[[i, j]] = rng.gen_range(-1.0..1.0);
            }
        }
        y_test[i] = if is_positive { 1.0 } else { 0.0 };
    }
    
    // Full workflow
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    // Train
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    // Predict
    let predictions = model.predict_proba(x_test.view()).unwrap();
    
    // Evaluate
    let roc_auc = calculate_roc_auc(y_test.as_slice(), predictions.as_slice());
    let pr_auc = calculate_pr_auc(y_test.as_slice(), predictions.as_slice());
    
    // Assertions
    assert!(roc_auc > 0.5, "ROC-AUC should be > 0.5: {}", roc_auc);
    assert!(pr_auc > 0.0, "PR-AUC should be > 0.0: {}", pr_auc);
    
    // Check predictions are valid
    for &p in predictions.iter() {
        assert!(p >= 0.0 && p <= 1.0, "Invalid probability: {}", p);
    }
}

#[test]
fn test_model_serialization() {
    use pkboost::*;
    use ndarray::{Array1, Array2};
    
    // Create and train a model
    let (x_train, y_train) = create_simple_data();
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    // Serialize
    let json = serde_json::to_string(&model).unwrap();
    assert!(!json.is_empty(), "Serialization should produce non-empty JSON");
    
    // Deserialize
    let model_loaded: OptimizedPKBoostShannon = serde_json::from_str(&json).unwrap();
    
    // Test that loaded model produces same predictions
    let (x_test, _) = create_simple_data();
    let preds_original = model.predict_proba(x_test.view()).unwrap();
    let preds_loaded = model_loaded.predict_proba(x_test.view()).unwrap();
    
    for (p1, p2) in preds_original.iter().zip(preds_loaded.iter()) {
        assert!((p1 - p2).abs() < 1e-10, "Predictions should match after serialization");
    }
}

fn create_simple_data() -> (Array2<f64>, Array1<f64>) {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let n = 200;
    let mut x = Array2::zeros((n, 5));
    let mut y = Array1::zeros(n);
    
    for i in 0..n {
        for j in 0..5 {
            x[[i, j]] = rng.gen_range(-1.0..1.0);
        }
        y[i] = if i < n / 5 { 1.0 } else { 0.0 };
    }
    
    (x, y)
}

#[test]
fn test_feature_usage() {
    let (x_train, y_train) = create_simple_data();
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    // Should be able to get feature usage
    let usage = model.get_feature_usage();
    assert_eq!(usage.len(), x_train.ncols(), "Feature usage length mismatch");
    
    // All usage counts should be non-negative
    for &count in usage.iter() {
        assert!(count >= 0, "Feature usage should be non-negative: {}", count);
    }
}

#[test]
fn test_early_stopping() {
    let (x_train, y_train) = create_simple_data();
    let (x_val, y_val) = create_simple_data();
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    let initial_n_estimators = model.n_estimators;
    
    model.fit(
        x_train.view(),
        y_train.view(),
        Some((x_val.view(), y_val.view())),
        false
    ).unwrap();
    
    // With early stopping, model might stop before n_estimators
    // This is a sanity check - exact behavior depends on validation performance
    assert!(model.trees.len() <= initial_n_estimators, 
            "Should not exceed n_estimators");
}
