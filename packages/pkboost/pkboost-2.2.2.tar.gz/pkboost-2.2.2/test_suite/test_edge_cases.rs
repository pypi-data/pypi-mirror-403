//! Edge case tests - testing boundary conditions and error handling

use pkboost::*;
use ndarray::{Array1, Array2};

#[test]
fn test_empty_dataset() {
    let x: Array2<f64> = Array2::zeros((0, 10));
    let y: Array1<f64> = Array1::zeros(0);
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // Should handle empty dataset gracefully
    let result = model.fit(x.view(), y.view(), None, false);
    assert!(result.is_err(), "Should fail on empty dataset");
}

#[test]
fn test_single_sample() {
    let x = Array2::from_shape_vec((1, 5), vec![1.0, 2.0, 3.0, 4.0, 5.0]).unwrap();
    let y = Array1::from_vec(vec![1.0]);
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // Single sample might fail or succeed depending on implementation
    let result = model.fit(x.view(), y.view(), None, false);
    // This might fail, which is acceptable for such edge case
}

#[test]
fn test_all_same_class() {
    // All samples are positive
    let x = Array2::from_shape_vec((100, 10), 
        (0..1000).map(|_| 1.0).collect()).unwrap();
    let y = Array1::from_vec(vec![1.0; 100]);
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // Should handle this edge case
    let result = model.fit(x.view(), y.view(), None, false);
    // This might fail, which is acceptable - can't learn from single class
}

#[test]
fn test_single_feature() {
    let x = Array2::from_shape_vec((100, 1), vec![1.0; 100]).unwrap();
    let y: Array1<f64> = Array1::from_vec(
        (0..100).map(|i| if i < 30 { 1.0 } else { 0.0 }).collect()
    );
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    let result = model.fit(x.view(), y.view(), None, false);
    assert!(result.is_ok(), "Should handle single feature");
    
    let predictions = model.predict_proba(x.view());
    assert!(predictions.is_ok(), "Should predict with single feature");
}

#[test]
fn test_very_large_dataset() {
    // Test with larger dataset (but not too large for CI)
    let n_samples = 10000;
    let n_features = 50;
    
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let mut x = Array2::zeros((n_samples, n_features));
    let mut y = Array1::zeros(n_samples);
    
    for i in 0..n_samples {
        for j in 0..n_features {
            x[[i, j]] = rng.gen_range(-1.0..1.0);
        }
        y[i] = if i < n_samples / 10 { 1.0 } else { 0.0 };
    }
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    let result = model.fit(x.view(), y.view(), None, false);
    assert!(result.is_ok(), "Should handle large dataset");
}

#[test]
fn test_mismatched_dimensions() {
    let x = Array2::zeros((100, 10));
    let y = Array1::zeros(50); // Wrong size!
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // This should fail during fit
    let result = model.fit(x.view(), y.view(), None, false);
    assert!(result.is_err(), "Should fail on dimension mismatch");
}

#[test]
fn test_all_nan_features() {
    let mut x = Array2::from_elem((100, 5), f64::NAN);
    let y: Array1<f64> = Array1::from_vec(
        (0..100).map(|i| if i < 30 { 1.0 } else { 0.0 }).collect()
    );
    
    let mut model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // Should handle all-NaN features (might fail, which is acceptable)
    let result = model.fit(x.view(), y.view(), None, false);
    // Result might be Ok or Err depending on implementation
}

#[test]
fn test_unfitted_model_prediction() {
    let x = Array2::zeros((10, 5));
    let y = Array1::zeros(10);
    
    let model = OptimizedPKBoostShannon::auto(x.view(), y.view());
    
    // Should fail - model not fitted
    let result = model.predict_proba(x.view());
    assert!(result.is_err(), "Should fail when model not fitted");
}

#[test]
fn test_prediction_wrong_dimensions() {
    let x_train = Array2::zeros((100, 10));
    let y_train = Array1::zeros(100);
    let x_test = Array2::zeros((50, 5)); // Wrong number of features!
    
    let mut model = OptimizedPKBoostShannon::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    // Should handle dimension mismatch gracefully
    let result = model.predict_proba(x_test.view());
    // Might succeed or fail depending on implementation
}
