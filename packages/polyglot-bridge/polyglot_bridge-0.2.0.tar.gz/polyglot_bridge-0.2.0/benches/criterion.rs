use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};
use std::hint::black_box;

// Note: Benchmarks use internal modules directly
// For production use, import from polyglot_bridge Python module
mod core {
    pub mod math {
        use crate::BridgeError;
        
        pub fn sum_of_squares(numbers: &[f64]) -> Result<f64, BridgeError> {
            if numbers.is_empty() {
                return Err(BridgeError::EmptyInput);
            }
            Ok(numbers.iter().map(|x| x * x).sum())
        }
        
        pub fn matrix_multiply(a: &[Vec<f64>], b: &[Vec<f64>]) -> Result<Vec<Vec<f64>>, BridgeError> {
            if a.is_empty() || b.is_empty() {
                return Err(BridgeError::EmptyInput);
            }
            
            let rows_a = a.len();
            let cols_a = a[0].len();
            let rows_b = b.len();
            let cols_b = b[0].len();
            
            if cols_a != rows_b {
                return Err(BridgeError::DimensionMismatch);
            }
            
            let mut result = vec![vec![0.0; cols_b]; rows_a];
            
            for i in 0..rows_a {
                for j in 0..cols_b {
                    for k in 0..cols_a {
                        result[i][j] += a[i][k] * b[k][j];
                    }
                }
            }
            
            Ok(result)
        }
    }
    
    pub mod parallel {
        use crate::BridgeError;
        use rayon::prelude::*;
        
        pub fn parallel_transform(data: &[f64], factor: f64) -> Result<Vec<f64>, BridgeError> {
            if data.is_empty() {
                return Err(BridgeError::EmptyInput);
            }
            Ok(data.par_iter().map(|&x| x * factor).collect())
        }
    }
}

#[derive(Debug)]
enum BridgeError {
    EmptyInput,
    DimensionMismatch,
}

use core::{math, parallel};

fn benchmark_sum_of_squares(c: &mut Criterion) {
    let mut group = c.benchmark_group("sum_of_squares");
    
    for size in [1_000, 10_000, 100_000].iter() {
        let data: Vec<f64> = (0..*size).map(|x| x as f64).collect();
        
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, _| {
            b.iter(|| math::sum_of_squares(black_box(&data)))
        });
    }
    
    group.finish();
}

fn benchmark_matrix_multiply(c: &mut Criterion) {
    let mut group = c.benchmark_group("matrix_multiply");
    
    for size in [10, 50, 100].iter() {
        let a: Vec<Vec<f64>> = (0..*size)
            .map(|i| (0..*size).map(|j| (i * size + j) as f64).collect())
            .collect();
        let b: Vec<Vec<f64>> = (0..*size)
            .map(|i| (0..*size).map(|j| (i * size + j) as f64).collect())
            .collect();
        
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |bench, _| {
            bench.iter(|| math::matrix_multiply(black_box(&a), black_box(&b)))
        });
    }
    
    group.finish();
}

fn benchmark_parallel_transform(c: &mut Criterion) {
    let mut group = c.benchmark_group("parallel_transform");
    
    for size in [1_000, 10_000, 100_000].iter() {
        let data: Vec<f64> = (0..*size).map(|x| x as f64).collect();
        let factor = 2.5;
        
        group.bench_with_input(BenchmarkId::from_parameter(size), size, |b, _| {
            b.iter(|| parallel::parallel_transform(black_box(&data), black_box(factor)))
        });
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_sum_of_squares, benchmark_matrix_multiply, benchmark_parallel_transform);
criterion_main!(benches);
