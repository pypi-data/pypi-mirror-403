use rayon::prelude::*;
use crate::error::BridgeError;

/// Transform data in parallel using Rayon
pub fn parallel_transform(data: &[f64], factor: f64) -> Result<Vec<f64>, BridgeError> {
    if data.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    let result: Vec<f64> = data.par_iter()
        .map(|&x| x * factor)
        .collect();
    
    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn test_parallel_transform_basic() {
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = parallel_transform(&data, 2.0).unwrap();
        assert_eq!(result, vec![2.0, 4.0, 6.0, 8.0, 10.0]);
    }

    #[test]
    fn test_parallel_transform_empty() {
        let data: Vec<f64> = vec![];
        let result = parallel_transform(&data, 2.0);
        assert!(matches!(result, Err(BridgeError::EmptyInput)));
    }

    #[test]
    fn test_parallel_transform_large_dataset() {
        let data: Vec<f64> = (0..10000).map(|x| x as f64).collect();
        let result = parallel_transform(&data, 3.0).unwrap();
        assert_eq!(result.len(), 10000);
        assert_eq!(result[0], 0.0);
        assert_eq!(result[9999], 29997.0);
    }

    // Feature: polyglot-bridge, Property 6: Algorithmic Equivalence
    // Validates: Requirements 5.1
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(100))]
        
        #[test]
        fn test_parallel_transform_algorithmic_equivalence(
            data in prop::collection::vec(-1e100..1e100, 1..1000),
            factor in -1e100..1e100
        ) {
            // Compare parallel and sequential implementations
            let parallel_result = parallel_transform(&data, factor);
            
            // Sequential implementation
            let sequential_result: Vec<f64> = data.iter()
                .map(|&x| x * factor)
                .collect();
            
            // Both should succeed
            prop_assert!(parallel_result.is_ok());
            let parallel = parallel_result.unwrap();
            
            // Verify results are identical
            prop_assert_eq!(parallel.len(), sequential_result.len());
            for (p, s) in parallel.iter().zip(sequential_result.iter()) {
                if p.is_finite() && s.is_finite() {
                    prop_assert!((p - s).abs() < 1e-10 || (p - s).abs() / s.abs() < 1e-10);
                } else {
                    prop_assert_eq!(p, s);
                }
            }
        }
    }
}
