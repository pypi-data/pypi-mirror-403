use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use polyglot_bridge::core::{math, parallel};

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
