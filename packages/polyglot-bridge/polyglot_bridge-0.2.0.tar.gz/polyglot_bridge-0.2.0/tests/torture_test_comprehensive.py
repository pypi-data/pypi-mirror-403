"""
🔥 THE ULTIMATE TORTURE TEST SUITE 🔥

This test suite is designed to BREAK our library and expose every weakness.
We test against:
1. NumPy (the giant we claim to beat)
2. Polars (the Rust-based DataFrame king)
3. orjson (fastest JSON serializer, Rust-based)
4. Pure Python (the baseline)

Test Categories:
- WEAKNESS TESTS: Where we expect to LOSE (small data, FFI overhead, memory pressure)
- STRENGTH TESTS: Where we expect to DOMINATE (fused ops, parallel transforms, zero-copy)
- STABILITY TESTS: Thread contention, memory leaks, edge cases

NO MERCY. NO EXCUSES. ONLY TRUTH.
"""

import numpy as np
import polyglot_bridge
import time
import sys
import gc
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Any

# Try to import competitors (graceful degradation if not installed)
try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False
    print("⚠️  Polars not installed. Skipping Polars benchmarks.")

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    print("⚠️  orjson not installed. Skipping orjson benchmarks.")


class TortureTest:
    """The Torture Master"""
    
    def __init__(self):
        self.results = []
        self.process = psutil.Process(os.getpid())
        
    def measure_time(self, func: Callable, *args, **kwargs) -> tuple[Any, float]:
        """Measure execution time in milliseconds"""
        gc.collect()  # Clean slate
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed
    
    def measure_memory(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def print_result(self, test_name: str, library: str, time_ms: float, 
                     baseline_ms: float = None, memory_mb: float = None):
        """Print formatted result"""
        speedup = ""
        if baseline_ms and baseline_ms > 0:
            ratio = baseline_ms / time_ms
            if ratio > 1:
                speedup = f" | 🚀 {ratio:.2f}x FASTER"
            else:
                speedup = f" | 🐌 {1/ratio:.2f}x SLOWER"
        
        mem_str = f" | RAM: {memory_mb:.1f}MB" if memory_mb else ""
        print(f"   {library:20s}: {time_ms:8.2f}ms{speedup}{mem_str}")
        
        self.results.append({
            'test': test_name,
            'library': library,
            'time_ms': time_ms,
            'memory_mb': memory_mb,
            'speedup': baseline_ms / time_ms if baseline_ms else 1.0
        })
    
    # ========================================================================
    # WEAKNESS TESTS: Where we expect to LOSE
    # ========================================================================
    
    def test_small_data_overhead(self):
        """
        TEST 1: Small Data FFI Overhead
        
        HYPOTHESIS: We will LOSE badly here.
        NumPy is optimized for small operations. Our FFI overhead will dominate.
        """
        print("\n" + "="*80)
        print("🔥 TEST 1: SMALL DATA OVERHEAD (3×3 Matrix, 100K iterations)")
        print("   Expected: NumPy WINS (FFI overhead kills us)")
        print("="*80)
        
        iterations = 100_000
        a_small = np.random.rand(3, 3).astype(np.float32)
        b_small = np.random.rand(3, 3).astype(np.float32)
        
        # NumPy baseline
        _, numpy_time = self.measure_time(
            lambda: [np.dot(a_small, b_small) for _ in range(iterations)]
        )
        self.print_result("Small Data", "NumPy", numpy_time)
        
        # Polyglot Bridge (List-based - WORST CASE)
        a_list = a_small.tolist()
        b_list = b_small.tolist()
        _, polyglot_list_time = self.measure_time(
            lambda: [polyglot_bridge.matrix_multiply(a_list, b_list) for _ in range(iterations)]
        )
        self.print_result("Small Data", "Polyglot (List)", polyglot_list_time, numpy_time)
        
        # Polyglot Bridge (NumPy zero-copy - BEST CASE)
        _, polyglot_numpy_time = self.measure_time(
            lambda: [polyglot_bridge.matmul_numpy_f32(a_small, b_small) for _ in range(iterations)]
        )
        self.print_result("Small Data", "Polyglot (Zero-Copy)", polyglot_numpy_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_numpy_time > numpy_time:
            print(f"   ❌ We LOST. NumPy is {numpy_time/polyglot_numpy_time:.2f}x faster.")
            print("   📝 LESSON: Don't use Polyglot Bridge for tiny repeated operations.")
        else:
            print(f"   ✅ UNEXPECTED WIN! We're {polyglot_numpy_time/numpy_time:.2f}x faster!")
    
    def test_non_contiguous_memory(self):
        """
        TEST 2: Non-Contiguous Memory (Strided Arrays)
        
        HYPOTHESIS: NumPy handles strides better than us.
        """
        print("\n" + "="*80)
        print("🔥 TEST 2: NON-CONTIGUOUS MEMORY (Strided Slices)")
        print("   Expected: NumPy WINS (optimized for strides)")
        print("="*80)
        
        big_mat = np.random.rand(2000, 2000).astype(np.float32)
        slice_a = big_mat[::2, ::2]  # Every other element (non-contiguous)
        slice_b = big_mat[::2, ::2]
        
        print(f"   Matrix shape: {slice_a.shape}, Contiguous: {slice_a.flags['C_CONTIGUOUS']}")
        
        # NumPy baseline
        _, numpy_time = self.measure_time(np.dot, slice_a, slice_b)
        self.print_result("Strided Memory", "NumPy", numpy_time)
        
        # Polyglot Bridge (must convert to list - EXPENSIVE)
        _, polyglot_time = self.measure_time(
            lambda: polyglot_bridge.matmul_numpy_f32(
                np.ascontiguousarray(slice_a), 
                np.ascontiguousarray(slice_b)
            )
        )
        self.print_result("Strided Memory", "Polyglot (Contiguous)", polyglot_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_time > numpy_time:
            print(f"   ❌ We LOST. NumPy handles strides {numpy_time/polyglot_time:.2f}x better.")
            print("   📝 LESSON: Ensure contiguous arrays before calling Polyglot Bridge.")
    
    def test_memory_pressure(self):
        """
        TEST 3: Memory Pressure Test
        
        HYPOTHESIS: Rayon's thread overhead might cause OOM faster than NumPy.
        """
        print("\n" + "="*80)
        print("🔥 TEST 3: MEMORY PRESSURE (Large Allocations)")
        print("   Expected: NumPy WINS (more memory efficient)")
        print("="*80)
        
        # Calculate safe size (use 30% of available RAM)
        available_ram_mb = psutil.virtual_memory().available / 1024 / 1024
        safe_size = int((available_ram_mb * 0.3 * 1024 * 1024 / 8) ** 0.5)  # Square matrix
        safe_size = min(safe_size, 10000)  # Cap at 10K×10K
        
        print(f"   Available RAM: {available_ram_mb:.0f}MB")
        print(f"   Test size: {safe_size}×{safe_size} (f64)")
        
        a_large = np.random.rand(safe_size, safe_size)
        b_large = np.random.rand(safe_size, safe_size)
        
        # NumPy baseline
        mem_before = self.measure_memory()
        _, numpy_time = self.measure_time(np.dot, a_large, b_large)
        mem_after = self.measure_memory()
        numpy_mem = mem_after - mem_before
        self.print_result("Memory Pressure", "NumPy", numpy_time, memory_mb=numpy_mem)
        
        # Polyglot Bridge
        gc.collect()
        mem_before = self.measure_memory()
        _, polyglot_time = self.measure_time(
            polyglot_bridge.matmul_numpy, a_large, b_large
        )
        mem_after = self.measure_memory()
        polyglot_mem = mem_after - mem_before
        self.print_result("Memory Pressure", "Polyglot", polyglot_time, numpy_time, polyglot_mem)
        
        print("\n💡 VERDICT:")
        if polyglot_mem > numpy_mem * 1.5:
            print(f"   ⚠️  We use {polyglot_mem/numpy_mem:.2f}x more memory than NumPy.")
            print("   📝 LESSON: Rayon thread overhead is real. Monitor memory in production.")
        else:
            print(f"   ✅ Memory usage is acceptable ({polyglot_mem/numpy_mem:.2f}x NumPy).")
    
    def test_thread_contention(self):
        """
        TEST 4: Thread Contention (Multithreaded Environment)
        
        HYPOTHESIS: Rust threads might conflict with Python threads.
        """
        print("\n" + "="*80)
        print("🔥 TEST 4: THREAD CONTENTION (Concurrent Execution)")
        print("   Expected: Potential slowdown or deadlock")
        print("="*80)
        
        def worker_numpy(worker_id):
            a = np.random.rand(500, 500)
            b = np.random.rand(500, 500)
            for _ in range(10):
                _ = np.dot(a, b)
            return worker_id
        
        def worker_polyglot(worker_id):
            a = np.random.rand(500, 500)
            b = np.random.rand(500, 500)
            for _ in range(10):
                _ = polyglot_bridge.matmul_numpy(a, b)
            return worker_id
        
        num_workers = 8
        
        # NumPy with ThreadPoolExecutor
        _, numpy_time = self.measure_time(
            lambda: list(ThreadPoolExecutor(max_workers=num_workers).map(
                worker_numpy, range(num_workers)
            ))
        )
        self.print_result("Thread Contention", "NumPy (8 threads)", numpy_time)
        
        # Polyglot Bridge with ThreadPoolExecutor
        _, polyglot_time = self.measure_time(
            lambda: list(ThreadPoolExecutor(max_workers=num_workers).map(
                worker_polyglot, range(num_workers)
            ))
        )
        self.print_result("Thread Contention", "Polyglot (8 threads)", polyglot_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_time > numpy_time * 2:
            print(f"   ⚠️  Severe thread contention detected ({polyglot_time/numpy_time:.2f}x slower).")
            print("   📝 LESSON: Use ProcessPoolExecutor instead of ThreadPoolExecutor.")
        else:
            print(f"   ✅ Thread safety is acceptable ({polyglot_time/numpy_time:.2f}x NumPy).")
    
    # ========================================================================
    # STRENGTH TESTS: Where we expect to DOMINATE
    # ========================================================================
    
    def test_fused_operations_dominance(self):
        """
        TEST 5: Fused Operations (Our Secret Weapon)
        
        HYPOTHESIS: We DOMINATE here. NumPy can't fuse operations.
        """
        print("\n" + "="*80)
        print("🔥 TEST 5: FUSED OPERATIONS (Our Secret Weapon)")
        print("   Expected: Polyglot Bridge DOMINATES")
        print("="*80)
        
        batch_size = 1000
        in_features = 512
        out_features = 256
        
        input_data = np.random.randn(batch_size, in_features).astype(np.float64)
        weights = np.random.randn(in_features, out_features).astype(np.float64)
        bias = np.random.randn(out_features).astype(np.float64)
        
        # NumPy (separate operations)
        def numpy_linear_relu():
            output = np.dot(input_data, weights) + bias
            return np.maximum(0, output)
        
        _, numpy_time = self.measure_time(numpy_linear_relu)
        self.print_result("Fused Linear+ReLU", "NumPy (separate)", numpy_time)
        
        # Polyglot Bridge (fused)
        _, polyglot_time = self.measure_time(
            polyglot_bridge.fused_linear_relu, input_data, weights, bias
        )
        self.print_result("Fused Linear+ReLU", "Polyglot (fused)", polyglot_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_time < numpy_time:
            print(f"   ✅ WE DOMINATE! {numpy_time/polyglot_time:.2f}x faster than NumPy!")
            print("   🎯 This is our KILLER FEATURE for ML inference.")
        else:
            print(f"   ❌ UNEXPECTED LOSS. NumPy is {polyglot_time/numpy_time:.2f}x faster.")
    
    def test_parallel_transform_scaling(self):
        """
        TEST 6: Parallel Transform Scaling
        
        HYPOTHESIS: We scale better with CPU cores than NumPy.
        """
        print("\n" + "="*80)
        print("🔥 TEST 6: PARALLEL TRANSFORM SCALING")
        print("   Expected: Polyglot Bridge scales better with cores")
        print("="*80)
        
        data_size = 10_000_000
        data = np.random.rand(data_size).astype(np.float64)
        factor = 2.5
        
        # NumPy (single-threaded for element-wise ops)
        _, numpy_time = self.measure_time(lambda: data * factor)
        self.print_result("Parallel Transform", "NumPy", numpy_time)
        
        # Polyglot Bridge (Rayon parallel)
        _, polyglot_time = self.measure_time(
            polyglot_bridge.parallel_map_numpy, data, factor
        )
        self.print_result("Parallel Transform", "Polyglot (Rayon)", polyglot_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_time < numpy_time:
            print(f"   ✅ WE WIN! {numpy_time/polyglot_time:.2f}x faster with parallelization!")
        else:
            print(f"   ⚠️  NumPy is {polyglot_time/numpy_time:.2f}x faster (vectorization wins).")
    
    def test_large_matrix_multiplication(self):
        """
        TEST 7: Large Matrix Multiplication (Our Sweet Spot)
        
        HYPOTHESIS: We dominate on large matrices with f32.
        """
        print("\n" + "="*80)
        print("🔥 TEST 7: LARGE MATRIX MULTIPLICATION (1000×1000 f32)")
        print("   Expected: Polyglot Bridge DOMINATES")
        print("="*80)
        
        size = 1000
        a = np.random.rand(size, size).astype(np.float32)
        b = np.random.rand(size, size).astype(np.float32)
        
        # NumPy
        _, numpy_time = self.measure_time(np.dot, a, b)
        self.print_result("Large MatMul", "NumPy (f32)", numpy_time)
        
        # Polyglot Bridge
        _, polyglot_time = self.measure_time(
            polyglot_bridge.matmul_numpy_f32, a, b
        )
        self.print_result("Large MatMul", "Polyglot (f32)", polyglot_time, numpy_time)
        
        print("\n💡 VERDICT:")
        if polyglot_time < numpy_time:
            print(f"   ✅ WE DOMINATE! {numpy_time/polyglot_time:.2f}x faster!")
            print("   🎯 This is our FLAGSHIP benchmark.")
        else:
            print(f"   ❌ NumPy wins by {polyglot_time/numpy_time:.2f}x.")
    
    # ========================================================================
    # COMPETITOR TESTS: vs Polars, orjson
    # ========================================================================
    
    def test_vs_polars(self):
        """
        TEST 8: DataFrame Operations vs Polars
        
        HYPOTHESIS: Polars wins on DataFrame ops, we win on raw compute.
        """
        if not HAS_POLARS:
            print("\n⚠️  Skipping Polars test (not installed)")
            return
        
        print("\n" + "="*80)
        print("🔥 TEST 8: VS POLARS (DataFrame Operations)")
        print("   Expected: Polars WINS (their domain), we win on raw compute")
        print("="*80)
        
        # Create test data
        size = 1_000_000
        df_data = {
            'a': np.random.rand(size),
            'b': np.random.rand(size),
        }
        
        # Polars: Column multiplication
        df_polars = pl.DataFrame(df_data)
        _, polars_time = self.measure_time(
            lambda: df_polars.with_columns((pl.col('a') * pl.col('b')).alias('c'))
        )
        self.print_result("Column Multiply", "Polars", polars_time)
        
        # Polyglot Bridge: Raw array multiplication
        a_array = df_data['a']
        b_array = df_data['b']
        _, polyglot_time = self.measure_time(
            lambda: a_array * b_array  # NumPy baseline
        )
        self.print_result("Column Multiply", "NumPy", polyglot_time, polars_time)
        
        # Polyglot Bridge: Parallel transform
        _, polyglot_parallel_time = self.measure_time(
            polyglot_bridge.parallel_map_numpy, a_array, 2.0
        )
        self.print_result("Column Multiply", "Polyglot (parallel)", polyglot_parallel_time, polars_time)
        
        print("\n💡 VERDICT:")
        print("   📝 Different use cases: Polars for DataFrames, Polyglot for raw compute.")
    
    def test_serialization_overhead(self):
        """
        TEST 9: Serialization Overhead (vs orjson)
        
        HYPOTHESIS: orjson dominates JSON, we dominate numerical compute.
        """
        if not HAS_ORJSON:
            print("\n⚠️  Skipping orjson test (not installed)")
            return
        
        print("\n" + "="*80)
        print("🔥 TEST 9: SERIALIZATION OVERHEAD (vs orjson)")
        print("   Expected: orjson WINS (their domain)")
        print("="*80)
        
        # Create test data
        data = {
            'matrix': np.random.rand(100, 100).tolist(),
            'metadata': {'size': 100, 'type': 'float64'}
        }
        
        # orjson
        _, orjson_time = self.measure_time(orjson.dumps, data)
        self.print_result("JSON Serialization", "orjson", orjson_time)
        
        # Standard json
        import json
        _, json_time = self.measure_time(json.dumps, data)
        self.print_result("JSON Serialization", "stdlib json", json_time, orjson_time)
        
        print("\n💡 VERDICT:")
        print("   📝 Different domains: orjson for JSON, Polyglot for numerical compute.")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    def print_summary(self):
        """Print final summary"""
        print("\n" + "="*80)
        print("📊 TORTURE TEST SUMMARY")
        print("="*80)
        
        wins = sum(1 for r in self.results if 'Polyglot' in r['library'] and r['speedup'] > 1.0)
        losses = sum(1 for r in self.results if 'Polyglot' in r['library'] and r['speedup'] < 1.0)
        
        print(f"\n🏆 WINS: {wins}")
        print(f"❌ LOSSES: {losses}")
        
        print("\n🎯 WHERE WE DOMINATE:")
        for r in self.results:
            if 'Polyglot' in r['library'] and r['speedup'] > 2.0:
                print(f"   ✅ {r['test']:30s}: {r['speedup']:.2f}x faster")
        
        print("\n⚠️  WHERE WE STRUGGLE:")
        for r in self.results:
            if 'Polyglot' in r['library'] and r['speedup'] < 0.5:
                print(f"   ❌ {r['test']:30s}: {1/r['speedup']:.2f}x slower")
        
        print("\n" + "="*80)
        print("🔥 FINAL VERDICT:")
        print("="*80)
        print("""
Polyglot Bridge v0.2.0 is a SPECIALIZED TOOL, not a silver bullet.

✅ USE IT FOR:
   - Large matrix operations (>100×100)
   - Fused ML operations (linear+relu, layer norm, etc.)
   - Parallel transformations on large datasets
   - Production ML inference pipelines

❌ DON'T USE IT FOR:
   - Tiny repeated operations (<10×10 matrices)
   - Non-contiguous memory (stride operations)
   - DataFrame operations (use Polars instead)
   - JSON serialization (use orjson instead)

🎯 BOTTOM LINE: We're a JET FIGHTER, not a cargo plane.
   Fast, specialized, and deadly in the right hands.
        """)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                   🔥 THE ULTIMATE TORTURE TEST 🔥                        ║
║                                                                           ║
║                    Polyglot Bridge v0.2.0 Stress Test                    ║
║                                                                           ║
║   This test suite will BREAK our library and expose every weakness.      ║
║   NO MERCY. NO EXCUSES. ONLY TRUTH.                                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n📊 System Info:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   NumPy: {np.__version__}")
    print(f"   CPU Cores: {psutil.cpu_count()}")
    print(f"   RAM: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB")
    print(f"   Available RAM: {psutil.virtual_memory().available / 1024 / 1024 / 1024:.1f} GB")
    
    torture = TortureTest()
    
    # Run all tests
    torture.test_small_data_overhead()
    torture.test_non_contiguous_memory()
    torture.test_memory_pressure()
    torture.test_thread_contention()
    torture.test_fused_operations_dominance()
    torture.test_parallel_transform_scaling()
    torture.test_large_matrix_multiplication()
    torture.test_vs_polars()
    torture.test_serialization_overhead()
    
    # Print summary
    torture.print_summary()


if __name__ == "__main__":
    main()
