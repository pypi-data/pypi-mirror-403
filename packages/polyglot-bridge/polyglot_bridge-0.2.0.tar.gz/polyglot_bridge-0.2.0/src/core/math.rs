use crate::error::BridgeError;

/// Compute sum of squares with overflow checking
pub fn sum_of_squares(numbers: &[f64]) -> Result<f64, BridgeError> {
    if numbers.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    let result: f64 = numbers.iter()
        .map(|&x| x * x)
        .sum();
    
    if result.is_infinite() {
        return Err(BridgeError::Overflow);
    }
    
    Ok(result)
}

/// Compute matrix multiplication using iterator-based approach
/// 
/// This implementation uses iterators instead of manual indexing to:
/// - Avoid bounds checking overhead
/// - Enable better compiler optimizations and vectorization
/// - Follow idiomatic Rust patterns
pub fn matrix_multiply(a: &[Vec<f64>], b: &[Vec<f64>]) -> Result<Vec<Vec<f64>>, BridgeError> {
    // Validate dimensions
    if a.is_empty() || b.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    // Validate that all rows in A have the same length
    let cols_a = a[0].len();
    if cols_a == 0 || !a.iter().all(|row| row.len() == cols_a) {
        return Err(BridgeError::DimensionMismatch);
    }
    
    // Validate that all rows in B have the same length
    let cols_b = b[0].len();
    if cols_b == 0 || !b.iter().all(|row| row.len() == cols_b) {
        return Err(BridgeError::DimensionMismatch);
    }
    
    let rows_b = b.len();
    
    if cols_a != rows_b {
        return Err(BridgeError::DimensionMismatch);
    }
    
    // Perform multiplication using iterators
    // For each row in A, compute dot product with each column in B
    let result: Vec<Vec<f64>> = a.iter()
        .map(|row_a| {
            // For each column index in B
            (0..cols_b)
                .map(|col_idx| {
                    // Compute dot product of row_a with column col_idx of B
                    row_a.iter()
                        .zip(b.iter().map(|row_b| row_b[col_idx]))
                        .map(|(a_val, b_val)| a_val * b_val)
                        .sum()
                })
                .collect()
        })
        .collect();
    
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn test_sum_of_squares_basic() {
        let numbers = vec![1.0, 2.0, 3.0];
        let result = sum_of_squares(&numbers).unwrap();
        assert_eq!(result, 14.0);
    }

    #[test]
    fn test_sum_of_squares_empty() {
        let numbers: Vec<f64> = vec![];
        let result = sum_of_squares(&numbers);
        assert!(matches!(result, Err(BridgeError::EmptyInput)));
    }

    #[test]
    fn test_sum_of_squares_overflow() {
        let numbers = vec![f64::MAX, f64::MAX];
        let result = sum_of_squares(&numbers);
        assert!(matches!(result, Err(BridgeError::Overflow)));
    }

    #[test]
    fn test_matrix_multiply_basic() {
        // 2x3 matrix * 3x2 matrix = 2x2 matrix
        let a = vec![
            vec![1.0, 2.0, 3.0],
            vec![4.0, 5.0, 6.0],
        ];
        let b = vec![
            vec![7.0, 8.0],
            vec![9.0, 10.0],
            vec![11.0, 12.0],
        ];
        let result = matrix_multiply(&a, &b).unwrap();
        
        // Expected: [[58, 64], [139, 154]]
        assert_eq!(result[0][0], 58.0);
        assert_eq!(result[0][1], 64.0);
        assert_eq!(result[1][0], 139.0);
        assert_eq!(result[1][1], 154.0);
    }

    #[test]
    fn test_matrix_multiply_dimension_mismatch() {
        let a = vec![
            vec![1.0, 2.0],
        ];
        let b = vec![
            vec![3.0],
            vec![4.0],
            vec![5.0],
        ];
        let result = matrix_multiply(&a, &b);
        assert!(matches!(result, Err(BridgeError::DimensionMismatch)));
    }

    #[test]
    fn test_matrix_multiply_empty() {
        let a: Vec<Vec<f64>> = vec![];
        let b = vec![vec![1.0]];
        let result = matrix_multiply(&a, &b);
        assert!(matches!(result, Err(BridgeError::EmptyInput)));
        
        let a = vec![vec![1.0]];
        let b: Vec<Vec<f64>> = vec![];
        let result = matrix_multiply(&a, &b);
        assert!(matches!(result, Err(BridgeError::EmptyInput)));
    }

    #[test]
    fn test_matrix_multiply_jagged_matrix() {
        // Jagged matrix A (rows with different lengths)
        let a = vec![
            vec![1.0, 2.0],
            vec![3.0, 4.0, 5.0],  // Different length!
        ];
        let b = vec![vec![1.0], vec![2.0]];
        let result = matrix_multiply(&a, &b);
        assert!(matches!(result, Err(BridgeError::DimensionMismatch)));
        
        // Jagged matrix B
        let a = vec![vec![1.0, 2.0]];
        let b = vec![
            vec![1.0, 2.0],
            vec![3.0],  // Different length!
        ];
        let result = matrix_multiply(&a, &b);
        assert!(matches!(result, Err(BridgeError::DimensionMismatch)));
    }

    // Feature: polyglot-bridge, Property 6: Algorithmic Equivalence
    // Validates: Requirements 5.1
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(100))]
        
        #[test]
        fn test_sum_of_squares_algorithmic_equivalence(
            numbers in prop::collection::vec(
                // Constrain to range that won't overflow when squared
                // sqrt(f64::MAX) ≈ 1.34e154, use conservative range
                -1e100..1e100, 
                1..100
            )
        ) {
            // Compare Rust implementation with pure mathematical formula
            let rust_result = sum_of_squares(&numbers);
            
            // Pure mathematical formula: sum of (x * x)
            let expected: f64 = numbers.iter().map(|&x| x * x).sum();
            
            // Both should succeed for constrained floats
            prop_assert!(rust_result.is_ok());
            let result = rust_result.unwrap();
            
            // Check algorithmic equivalence
            prop_assert!(expected.is_finite());
            prop_assert!((result - expected).abs() < 1e-10 || (result - expected).abs() / expected.abs() < 1e-10);
        }
    }
}
