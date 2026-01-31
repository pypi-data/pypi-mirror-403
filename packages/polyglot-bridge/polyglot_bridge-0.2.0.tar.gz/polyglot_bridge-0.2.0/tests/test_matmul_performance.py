"""
Quick matmul performance test to verify BLAS integration
"""
import numpy as np
import polyglot_bridge
import time

def benchmark_matmul(size, dtype, iterations=10):
    """Benchmark matrix multiplication"""
    if dtype == np.float32:
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        poly_func = polyglot_bridge.matmul_numpy_f32
    else:
        a = np.random.rand(size, size).astype(np.float64)
        b = np.random.rand(size, size).astype(np.float64)
        poly_func = polyglot_bridge.matmul_numpy
    
    # Warmup
    _ = np.dot(a, b)
    _ = poly_func(a, b)
    
    # NumPy benchmark
    numpy_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        _ = np.dot(a, b)
        numpy_times.append((time.perf_counter() - start) * 1000)
    
    numpy_avg = sum(numpy_times) / len(numpy_times)
    
    # Polyglot benchmark
    poly_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        _ = poly_func(a, b)
        poly_times.append((time.perf_counter() - start) * 1000)
    
    poly_avg = sum(poly_times) / len(poly_times)
    
    print(f"\n{size}×{size} {dtype.__name__}:")
    print(f"  NumPy:    {numpy_avg:7.2f}ms (min: {min(numpy_times):.2f}ms)")
    print(f"  Polyglot: {poly_avg:7.2f}ms (min: {min(poly_times):.2f}ms)")
    
    if poly_avg < numpy_avg:
        print(f"  ✅ Polyglot WINS by {numpy_avg/poly_avg:.2f}x")
    else:
        print(f"  ❌ NumPy wins by {poly_avg/numpy_avg:.2f}x")
    
    return numpy_avg, poly_avg

print("="*60)
print("MATMUL PERFORMANCE TEST (with matrixmultiply)")
print("="*60)

# Test different sizes
for size in [100, 500, 1000, 2000]:
    benchmark_matmul(size, np.float32, iterations=5)

for size in [100, 500, 1000]:
    benchmark_matmul(size, np.float64, iterations=5)

print("\n" + "="*60)
print("ANALYSIS:")
print("="*60)
print("""
If Polyglot is still slower, possible reasons:
1. NumPy is using optimized BLAS (OpenBLAS/MKL)
2. matrixmultiply needs more tuning
3. FFI overhead dominates for these sizes

Our advantage is in FUSED operations, not pure matmul.
""")
