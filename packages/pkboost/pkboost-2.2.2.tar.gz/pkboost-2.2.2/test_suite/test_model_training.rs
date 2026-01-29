//! Unit tests for model training functionality
//! Tests that models can train correctly on various data scenarios

use pkboost::*;
use ndarray::{Array1, Array2};

fn create_synthetic_data(n_samples: usize, n_features: usize, pos_ratio: f64) -> (Array2<f64>, Array1<f64>) {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let mut x = Array2::zeros((n_samples, n_features));
    let mut y = Array1::zeros(n_samples);
    
    let n_positives = (n_samples as f64 * pos_ratio) as usize;
    
    for i in 0..n_samples {
        let is_positive = i < n_positives;
        
        // Generate features: positives have higher values in first feature
        for j in 0..n_features {
            if is_positive && j == 0 {
                x[[i, j]] = rng.gen_range(0.5..1.5);
            } else if !is_positive && j == 0 {
                x[[i, j]] = rng.gen_range(-1.5..0.5);
            } else {
                x[[i, j]] = rng.gen_range(-1.0..1.0);
            }
        }
        
        y[i] = if is_positive { 1.0 } else { 0.0 };
    }
    
    (x, y)
}

#[test]
fn test_model_trains_on_balanced_data() {
    let (x_train, y_train) = create_synthetic_data(1000, 10, 0.5);
    let (x_test, y_test) = create_synthetic_data(200, 10, 0.5);
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    // Training should succeed
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Model training failed");
    
    // Model should be fitted
    assert!(model.trees.len() > 0, "Model has no trees after training");
    
    // Should be able to predict
    let predictions = model.predict_proba(x_test.view());
    assert!(predictions.is_ok(), "Prediction failed");
    
    let preds = predictions.unwrap();
    assert_eq!(preds.len(), y_test.len(), "Prediction length mismatch");
    
    // Predictions should be probabilities (0-1 range)
    for &p in preds.iter() {
        assert!(p >= 0.0 && p <= 1.0, "Prediction out of range: {}", p);
    }
}

#[test]
fn test_model_trains_on_imbalanced_data() {
    // Extreme imbalance: 1% positive class
    let (x_train, y_train) = create_synthetic_data(10000, 10, 0.01);
    let (x_test, y_test) = create_synthetic_data(2000, 10, 0.01);
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Model training failed on imbalanced data");
    
    // Check that scale_pos_weight is set appropriately
    assert!(model.scale_pos_weight > 1.0, "scale_pos_weight should be > 1.0 for imbalanced data");
    
    let predictions = model.predict_proba(x_test.view()).unwrap();
    
    // Calculate PR-AUC (should be reasonable for imbalanced data)
    let pr_auc = calculate_pr_auc(y_test.as_slice(), predictions.as_slice());
    assert!(pr_auc > 0.3, "PR-AUC too low: {}", pr_auc);
}

#[test]
fn test_model_with_validation_set() {
    let (x_train, y_train) = create_synthetic_data(1000, 10, 0.3);
    let (x_val, y_val) = create_synthetic_data(200, 10, 0.3);
    let (x_test, y_test) = create_synthetic_data(200, 10, 0.3);
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    // Train with validation set for early stopping
    let result = model.fit(
        x_train.view(), 
        y_train.view(), 
        Some((x_val.view(), y_val.view())), 
        false
    );
    assert!(result.is_ok(), "Training with validation set failed");
    
    // Model should have stopped early (best_iteration < n_estimators)
    // Note: This might not always be true, but it's a good sanity check
    let predictions = model.predict_proba(x_test.view()).unwrap();
    let roc_auc = calculate_roc_auc(y_test.as_slice(), predictions.as_slice());
    assert!(roc_auc > 0.5, "ROC-AUC should be > 0.5: {}", roc_auc);
}

#[test]
fn test_model_handles_missing_values() {
    let (mut x_train, y_train) = create_synthetic_data(500, 5, 0.3);
    
    // Introduce some NaN values
    x_train[[0, 0]] = f64::NAN;
    x_train[[10, 2]] = f64::NAN;
    x_train[[50, 4]] = f64::NAN;
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    // Should handle NaN values gracefully
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Model should handle missing values");
}

#[test]
fn test_model_predictions_are_consistent() {
    let (x_train, y_train) = create_synthetic_data(500, 10, 0.3);
    let x_test = create_synthetic_data(100, 10, 0.3).0;
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    // Predict twice - should get same results
    let preds1 = model.predict_proba(x_test.view()).unwrap();
    let preds2 = model.predict_proba(x_test.view()).unwrap();
    
    for (p1, p2) in preds1.iter().zip(preds2.iter()) {
        assert!((p1 - p2).abs() < 1e-10, "Predictions should be consistent");
    }
}

#[test]
fn test_model_auto_tuning_sets_parameters() {
    let (x_train, y_train) = create_synthetic_data(5000, 20, 0.1);
    
    let model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    
    // Auto-tuned model should have reasonable parameters
    assert!(model.n_estimators > 0, "n_estimators should be set");
    assert!(model.learning_rate > 0.0 && model.learning_rate <= 1.0, "learning_rate invalid");
    assert!(model.max_depth > 0, "max_depth should be set");
    assert!(model.scale_pos_weight > 0.0, "scale_pos_weight should be set");
    assert!(model.is_auto_tuned(), "Model should be marked as auto-tuned");
}
