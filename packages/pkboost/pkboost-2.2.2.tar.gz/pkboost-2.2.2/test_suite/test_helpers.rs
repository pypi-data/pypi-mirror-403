//! Test suite helper module
//! Provides common utilities for tests

use ndarray::{Array1, Array2};
use rand::Rng;

/// Create synthetic binary classification data
pub fn create_binary_data(
    n_samples: usize,
    n_features: usize,
    pos_ratio: f64,
) -> (Array2<f64>, Array1<f64>) {
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

/// Create synthetic regression data
pub fn create_regression_data(
    n_samples: usize,
    n_features: usize,
) -> (Array2<f64>, Array1<f64>) {
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

/// Create synthetic multi-class data
pub fn create_multiclass_data(
    n_samples: usize,
    n_features: usize,
    n_classes: usize,
) -> (Array2<f64>, Array1<f64>) {
    let mut rng = rand::thread_rng();
    
    let mut x = Array2::zeros((n_samples, n_features));
    let mut y = Array1::zeros(n_samples);
    
    let samples_per_class = n_samples / n_classes;
    
    for class_idx in 0..n_classes {
        let start_idx = class_idx * samples_per_class;
        let end_idx = if class_idx == n_classes - 1 {
            n_samples
        } else {
            (class_idx + 1) * samples_per_class
        };
        
        for i in start_idx..end_idx {
            // Each class has different feature patterns
            for j in 0..n_features {
                let base_value = class_idx as f64 * 2.0;
                x[[i, j]] = base_value + rng.gen_range(-0.5..0.5);
            }
            y[i] = class_idx as f64;
        }
    }
    
    (x, y)
}
