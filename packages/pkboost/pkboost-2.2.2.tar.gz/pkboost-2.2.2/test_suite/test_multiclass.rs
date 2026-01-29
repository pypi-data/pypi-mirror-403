//! Tests for multi-class classification functionality

use pkboost::*;
use ndarray::{Array1, Array2};

fn create_multiclass_data(n_samples: usize, n_features: usize, n_classes: usize) -> (Array2<f64>, Array1<f64>) {
    use rand::Rng;
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

#[test]
fn test_multiclass_training() {
    let (x_train, y_train) = create_multiclass_data(600, 10, 3);
    let (x_test, y_test) = create_multiclass_data(200, 10, 3);
    
    let mut model = MultiClassPKBoost::new(3);
    
    let result = model.fit(x_train.view(), y_train.view(), None, false);
    assert!(result.is_ok(), "Multi-class training failed");
    
    // Should be able to predict
    let predictions = model.predict(x_test.view());
    assert!(predictions.is_ok(), "Multi-class prediction failed");
    
    let preds = predictions.unwrap();
    assert_eq!(preds.len(), y_test.len(), "Prediction length mismatch");
    
    // Predictions should be valid class indices
    for &pred in preds.iter() {
        assert!(pred < 3, "Prediction out of range: {}", pred);
    }
}

#[test]
fn test_multiclass_probabilities() {
    let (x_train, y_train) = create_multiclass_data(500, 10, 4);
    let (x_test, _) = create_multiclass_data(100, 10, 4);
    
    let mut model = MultiClassPKBoost::new(4);
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    let probs = model.predict_proba(x_test.view());
    assert!(probs.is_ok(), "Probability prediction failed");
    
    let prob_matrix = probs.unwrap();
    
    // Check shape: (n_samples, n_classes)
    assert_eq!(prob_matrix.nrows(), 100, "Wrong number of samples");
    assert_eq!(prob_matrix.ncols(), 4, "Wrong number of classes");
    
    // Check that probabilities sum to 1 for each sample
    for row in prob_matrix.rows() {
        let sum: f64 = row.iter().sum();
        assert!((sum - 1.0).abs() < 1e-6, "Probabilities don't sum to 1: {}", sum);
        
        // All probabilities should be in [0, 1]
        for &p in row.iter() {
            assert!(p >= 0.0 && p <= 1.0, "Probability out of range: {}", p);
        }
    }
}

#[test]
fn test_multiclass_accuracy() {
    let (x_train, y_train) = create_multiclass_data(1000, 15, 5);
    let (x_test, y_test) = create_multiclass_data(300, 15, 5);
    
    let mut model = MultiClassPKBoost::new(5);
    model.fit(x_train.view(), y_train.view(), None, false).unwrap();
    
    let predictions = model.predict(x_test.view()).unwrap();
    let y_test_slice = y_test.as_slice();
    
    // Calculate accuracy
    let correct: usize = predictions.iter()
        .zip(y_test_slice.iter())
        .filter(|(&pred, &true_y)| pred == true_y as usize)
        .count();
    
    let accuracy = correct as f64 / predictions.len() as f64;
    
    // Should achieve reasonable accuracy on synthetic data
    assert!(accuracy > 0.3, "Accuracy too low: {}", accuracy);
}

#[test]
fn test_multiclass_imbalanced() {
    // Create imbalanced multi-class data
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    let n_samples = 1000;
    let n_features = 10;
    let n_classes = 3;
    
    let mut x = Array2::zeros((n_samples, n_features));
    let mut y = Array1::zeros(n_samples);
    
    // Class 0: 800 samples, Class 1: 150 samples, Class 2: 50 samples
    let class_sizes = [800, 150, 50];
    let mut idx = 0;
    
    for class_idx in 0..n_classes {
        for _ in 0..class_sizes[class_idx] {
            for j in 0..n_features {
                let base_value = class_idx as f64 * 2.0;
                x[[idx, j]] = base_value + rng.gen_range(-0.5..0.5);
            }
            y[idx] = class_idx as f64;
            idx += 1;
        }
    }
    
    let mut model = MultiClassPKBoost::new(n_classes);
    let result = model.fit(x.view(), y.view(), None, false);
    assert!(result.is_ok(), "Should handle imbalanced multi-class data");
}
