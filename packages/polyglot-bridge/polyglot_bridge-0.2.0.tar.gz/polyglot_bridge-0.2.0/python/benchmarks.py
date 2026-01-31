#!/usr/bin/env python3
"""
Performance Benchmarks: The Polyglot Bridge
Compare pure Python implementations vs Rust-powered functions
"""

import time
import polyglot_bridge
from typing import List


# ============================================================================
# PURE PYTHON IMPLEMENTATIONS (Fair & Optimized)
# ============================================================================

def python_sum_of_squares(numbers: List[float]) -> float:
    """Pure Python implementation of sum of squares"""
    return sum(x * x for x in numbers)


def python_matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """Pure Python implementation of matrix multiplication"""
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    
    result = [[0.0] * cols_b for _ in range(rows_a)]
    
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    
    return result


def python_transform(data: List[float], factor: float) -> List[float]:
    """Pure Python implementation of data transformation"""
    return [x * factor for x in data]


# ============================================================================
# BENCHMARK UTILITIES
# ============================================================================

def benchmark_function(func, *args, iterations=10):
    """Benchmark a function with multiple iterations"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args)
        end = time.perf_counter()
        times.append(end - start)
    
    # Remove outliers (fastest and slowest)
    if len(times) > 2:
        times.remove(min(times))
        times.remove(max(times))
    
    avg_time = sum(times) / len(times)
    return avg_time, result


# ============================================================================
# BENCHMARK SUITE
# ============================================================================

def run_benchmarks():
    """Run comprehensive benchmark suite"""
    
    print("=" * 80)
    print("🚀 THE POLYGLOT BRIDGE - PERFORMANCE SHOWDOWN 🚀")
    print("=" * 80)
    print()
    
    results = []
    
    # ========================================================================
    # BENCHMARK 1: sum_of_squares
    # ========================================================================
    print("📊 Benchmark 1: sum_of_squares")
    print("-" * 80)
    
    for size in [1_000, 10_000, 100_000]:
        data = list(range(size))
        
        # Python
        py_time, py_result = benchmark_function(python_sum_of_squares, data)
        
        # Rust
        rust_time, rust_result = benchmark_function(polyglot_bridge.sum_of_squares, data)
        
        speedup = py_time / rust_time
        
        print(f"  Size: {size:>7,} elements")
        print(f"    Python: {py_time*1000:>8.3f} ms")
        print(f"    Rust:   {rust_time*1000:>8.3f} ms")
        print(f"    Speedup: {speedup:>6.2f}x faster 🔥")
        print()
        
        results.append({
            'function': 'sum_of_squares',
            'size': size,
            'python_ms': py_time * 1000,
            'rust_ms': rust_time * 1000,
            'speedup': speedup
        })
    
    # ========================================================================
    # BENCHMARK 2: matrix_multiply
    # ========================================================================
    print("📊 Benchmark 2: matrix_multiply")
    print("-" * 80)
    
    for size in [10, 50, 100]:
        a = [[float(i * size + j) for j in range(size)] for i in range(size)]
        b = [[float(i * size + j) for j in range(size)] for i in range(size)]
        
        # Python
        py_time, py_result = benchmark_function(python_matrix_multiply, a, b, iterations=5)
        
        # Rust
        rust_time, rust_result = benchmark_function(polyglot_bridge.matrix_multiply, a, b, iterations=5)
        
        speedup = py_time / rust_time
        
        print(f"  Size: {size:>3}x{size} matrices")
        print(f"    Python: {py_time*1000:>8.3f} ms")
        print(f"    Rust:   {rust_time*1000:>8.3f} ms")
        print(f"    Speedup: {speedup:>6.2f}x faster 🔥")
        print()
        
        results.append({
            'function': 'matrix_multiply',
            'size': f'{size}x{size}',
            'python_ms': py_time * 1000,
            'rust_ms': rust_time * 1000,
            'speedup': speedup
        })
    
    # ========================================================================
    # BENCHMARK 3: parallel_transform
    # ========================================================================
    print("📊 Benchmark 3: parallel_transform")
    print("-" * 80)
    
    factor = 2.5
    for size in [1_000, 10_000, 100_000]:
        data = list(range(size))
        
        # Python
        py_time, py_result = benchmark_function(python_transform, data, factor)
        
        # Rust (with Rayon parallelization)
        rust_time, rust_result = benchmark_function(polyglot_bridge.parallel_transform, data, factor)
        
        speedup = py_time / rust_time
        
        print(f"  Size: {size:>7,} elements")
        print(f"    Python: {py_time*1000:>8.3f} ms")
        print(f"    Rust:   {rust_time*1000:>8.3f} ms")
        print(f"    Speedup: {speedup:>6.2f}x faster 🔥")
        print()
        
        results.append({
            'function': 'parallel_transform',
            'size': size,
            'python_ms': py_time * 1000,
            'rust_ms': rust_time * 1000,
            'speedup': speedup
        })
    
    # ========================================================================
    # SUMMARY TABLE
    # ========================================================================
    print("=" * 80)
    print("📈 SUMMARY: SPEEDUP RATIOS")
    print("=" * 80)
    print()
    print(f"{'Function':<20} {'Size':<15} {'Python (ms)':<15} {'Rust (ms)':<15} {'Speedup':<10}")
    print("-" * 80)
    
    for r in results:
        size_str = str(r['size']) if isinstance(r['size'], int) else r['size']
        print(f"{r['function']:<20} {size_str:<15} {r['python_ms']:<15.3f} {r['rust_ms']:<15.3f} {r['speedup']:<10.2f}x")
    
    print()
    print("=" * 80)
    
    # Calculate average speedup
    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    max_speedup = max(r['speedup'] for r in results)
    
    print(f"🏆 Average Speedup: {avg_speedup:.2f}x")
    print(f"🚀 Maximum Speedup: {max_speedup:.2f}x")
    print("=" * 80)
    print()
    print("💡 Conclusion: Rust-powered functions deliver significant performance gains")
    print("   for computationally intensive operations, making them ideal for ML pipelines!")
    print()


if __name__ == "__main__":
    run_benchmarks()
