//! Tests for regression functionality

use pkboost::*;
use ndarray::{Array1, Array2};

fn create_regression_data(n_samples: usize, n_features: usize) -> (Array2<f64>, Array1<f64>) {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let mut x = Array2::zeros((n_samples, n_features));
    let mut y = Array1::zeros(n_samples);
    
    for i in 0..n_samples {
        let mut target = 0.0;
        
        for j in 0..n_features {
            let val = rng.gen_range(-1.0..1.0);
            x[[i, j]] = val;
            // Create linear relationship: y = sum of first 3 features + noise
            if j < 3 {
                target += val * (j as f64 + 1.0);
            }
        }
        
        // Add noise
        target += rng.gen_range(-0.1..0.1);
        y[i] = target;
    }
    
    (x, y)
}

#[test]
fn test_regression_training() {
    let (x_train, y_train) = create_regression_data(1000, 10);
    let (x_test, y_test) = create_regression_data(200, 10);
    
    let mut model = PKBoostRegressor::auto(x_train.view(), y_train.view());
    
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Regression training failed");
    
    let predictions = model.predict(x_test.view());
    assert!(predictions.is_ok(), "Regression prediction failed");
    
    let preds = predictions.unwrap();
    assert_eq!(preds.len(), y_test.len(), "Prediction length mismatch");
}

#[test]
fn test_regression_metrics() {
    let (x_train, y_train) = create_regression_data(1000, 10);
    let (x_test, y_test) = create_regression_data(200, 10);
    
    let mut model = PKBoostRegressor::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    let predictions = model.predict(x_test.view()).unwrap();
    let y_test_slice = y_test.as_slice();
    let preds_slice = predictions.as_slice().unwrap();
    
    // Calculate RMSE
    let rmse = calculate_rmse(y_test_slice, preds_slice);
    assert!(rmse.is_finite(), "RMSE should be finite");
    assert!(rmse >= 0.0, "RMSE should be non-negative");
    
    // Calculate R²
    let r2 = calculate_r2(y_test_slice, preds_slice);
    assert!(r2.is_finite(), "R² should be finite");
    
    // For synthetic data, R² should be reasonable
    // (might be negative if model is very bad, which is valid)
}

#[test]
fn test_regression_with_validation() {
    let (x_train, y_train) = create_regression_data(800, 10);
    let (x_val, y_val) = create_regression_data(200, 10);
    let (x_test, y_test) = create_regression_data(200, 10);
    
    let mut model = PKBoostRegressor::auto(x_train.view(), y_train.view());
    
    let result = model.fit(
        x_train.view(),
        y_train.view(),
        Some((x_val.view(), y_val.view())),
        false
    );
    assert!(result.is_ok(), "Regression with validation failed");
    
    let predictions = model.predict(x_test.view()).unwrap();
    let rmse = calculate_rmse(y_test.as_slice(), predictions.as_slice());
    assert!(rmse.is_finite() && rmse >= 0.0, "RMSE invalid: {}", rmse);
}

#[test]
fn test_regression_outliers() {
    let (mut x_train, mut y_train) = create_regression_data(500, 5);
    
    // Add some outliers
    y_train[0] = 1000.0;  // Extreme outlier
    y_train[1] = -1000.0; // Extreme negative
    
    let mut model = PKBoostRegressor::auto(x_train.view(), y_train.view());
    
    // Should handle outliers (might use Huber loss internally)
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Should handle outliers");
}

#[test]
fn test_regression_mae() {
    let (x_train, y_train) = create_regression_data(500, 10);
    let (x_test, y_test) = create_regression_data(100, 10);
    
    let mut model = PKBoostRegressor::auto(x_train.view(), y_train.view());
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    let predictions = model.predict(x_test.view()).unwrap();
    let mae = calculate_mae(y_test.as_slice(), predictions.as_slice());
    
    assert!(mae.is_finite() && mae >= 0.0, "MAE invalid: {}", mae);
}
