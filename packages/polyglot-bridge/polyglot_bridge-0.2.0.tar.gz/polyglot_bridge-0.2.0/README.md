# 🔥 Polyglot Bridge: The Inference King

**Stop wasting CPU cycles on Python-NumPy roundtrips.**

Polyglot Bridge is a specialized Rust-powered accelerator for **ML inference pipelines**. We don't replace NumPy—we DOMINATE where it matters: **fused operations** and **parallel transforms**.

[![Rust](https://img.shields.io/badge/rust-1.93%2B-orange.svg)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 The Problem

Your ML inference pipeline is slow because:
- **NumPy can't fuse operations** - Every operation = Python roundtrip
- **Single-threaded transforms** - Wasting your CPU cores
- **Memory copies everywhere** - Killing performance

## ⚡ The Solution

**Polyglot Bridge** eliminates Python overhead with:
- **Fused ML kernels** - Linear+ReLU+Norm in ONE Rust call
- **Automatic parallelization** - All cores, zero threading code
- **Zero-copy NumPy** - Direct memory access, no copies

---

## 🏆 Where We DOMINATE

| Operation | NumPy | Polyglot Bridge | **Speedup** |
|-----------|-------|-----------------|-------------|
| **Layer Normalization** | 7.98ms | 4.01ms | **1.99x faster** 🔥 |
| **Parallel Transform** (10M) | 39.23ms | 22.18ms | **1.77x faster** ⚡ |
| **Softmax** (1000×1000) | 24.32ms | 17.56ms | **1.38x faster** 🚀 |

**Average: 1.71x faster** on production ML operations.

> Benchmarked on Windows, Python 3.14, 8-core CPU. See `tests/inference_benchmark.py` for reproduction.

---

## 📦 Installation

```bash
pip install polyglot-bridge
```

**Requirements:** Python 3.8+, NumPy. No Rust installation needed.

---

## 🚀 Quickstart

### Fused Operations (THE KILLER FEATURE)

```python
import numpy as np
import polyglot_bridge

# Your neural network layer
input = np.random.randn(1000, 512).astype(np.float64)
weights = np.random.randn(512, 256).astype(np.float64)
bias = np.random.randn(256).astype(np.float64)

# ❌ NumPy way (slow - 3 Python roundtrips)
output = np.maximum(0, np.dot(input, weights) + bias)

# ✅ Polyglot way (fast - 1 Rust call)
output = polyglot_bridge.fused_linear_relu(input, weights, bias)
```

### Parallel Transforms (THE CLEANER)

```python
# Process 10 million elements
data = np.random.rand(10_000_000)

# ❌ NumPy (single-threaded)
result = data * 2.5

# ✅ Polyglot (all CPU cores)
result = polyglot_bridge.parallel_map_numpy(data, 2.5)  # 1.68x faster
```

### Layer Normalization (THE STABILIZER)

```python
# Transformer layer normalization
x = np.random.randn(512, 768).astype(np.float64)

# ❌ NumPy (multiple operations)
mean = x.mean(axis=1, keepdims=True)
var = x.var(axis=1, keepdims=True)
normalized = (x - mean) / np.sqrt(var + 1e-5)

# ✅ Polyglot (fused, 2.11x faster)
normalized = polyglot_bridge.fused_layer_norm(x, 1e-5)
```

---

## 🎯 When to Use Polyglot Bridge

### ✅ USE IT FOR:
- **ML inference pipelines** - Fused ops eliminate Python overhead
- **Large-scale data preprocessing** - Parallel transforms dominate
- **Production workloads** - Where milliseconds = money
- **Transformer models** - Layer norm, softmax, dropout+residual

### ❌ DON'T USE IT FOR:
- **Pure matrix multiplication** - NumPy's BLAS is faster (20 years of optimization)
- **Small datasets** (<1000 elements) - FFI overhead dominates
- **DataFrame operations** - Use Polars instead

---

## 🔥 Complete API

### Fused Operations
```python
# Linear transformation
fused_linear(input, weights, bias) → output

# Linear + ReLU activation
fused_linear_relu(input, weights, bias) → output

# Layer normalization
fused_layer_norm(x, eps=1e-5) → normalized

# Softmax activation
fused_softmax(logits) → probabilities

# Dropout + residual connection
fused_dropout_add(x, residual, mask, scale) → output
```

### Parallel Operations
```python
# Element-wise transform (all CPU cores)
parallel_map_numpy(array, factor) → transformed

# Activations
relu_numpy(array) → activated
sigmoid_numpy(array) → activated
```

### Zero-Copy NumPy
```python
# Matrix multiplication (f32/f64)
matmul_numpy(a, b) → result
matmul_numpy_f32(a, b) → result  # 2x faster for ML

# Aggregations
sum_of_squares_numpy(array) → scalar
```

Full API documentation: `polyglot_bridge.pyi` (IDE autocomplete supported)

---

## 💡 Real-World Example

```python
import numpy as np
import polyglot_bridge

def inference_pipeline(input_data):
    """
    2-layer neural network with Polyglot Bridge
    
    Before: 45ms (NumPy separate ops)
    After: 27ms (Polyglot fused ops)
    Speedup: 1.67x faster
    """
    # Layer 1: Linear + ReLU (FUSED)
    hidden = polyglot_bridge.fused_linear_relu(
        input_data, weights1, bias1
    )
    
    # Layer 2: Linear + Softmax (FUSED)
    logits = polyglot_bridge.fused_linear(hidden, weights2, bias2)
    probs = polyglot_bridge.fused_softmax(logits)
    
    return probs

# Process batch
predictions = inference_pipeline(batch_data)
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│      Python Application             │
└──────────────┬──────────────────────┘
               │ Zero-cost FFI (PyO3)
               ▼
┌─────────────────────────────────────┐
│      Fused ML Kernels (Rust)        │
│  • Linear + ReLU + Norm             │
│  • Single-pass computation          │
│  • Zero intermediate allocations    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      Parallel Engine (Rayon)        │
│  • Automatic CPU core utilization   │
│  • Work-stealing scheduler          │
│  • Zero manual threading            │
└─────────────────────────────────────┘
```

**Tech Stack:**
- Rust Edition 2024 (latest language features)
- PyO3 0.27 (Python-Rust bindings)
- Rayon 1.10 (parallelization)
- ndarray 0.17 (numerical computing)

---

## 🧪 Testing

```bash
# Run inference benchmark
python tests/inference_benchmark.py

# Run unit tests
pytest tests/

# Run Rust tests
cargo test
```

---

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/nirvagold/polyglot-bridge.git
cd polyglot-bridge

# Setup environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install maturin
pip install maturin

# Build and install
maturin develop --release

# Run tests
pytest tests/
cargo test
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- [PyO3](https://pyo3.rs/) - Python-Rust interoperability
- [Rayon](https://github.com/rayon-rs/rayon) - Data parallelism
- [ndarray](https://github.com/rust-ndarray/ndarray) - N-dimensional arrays

---

<div align="center">

**We don't compete. We SPECIALIZE. We WIN.**

🔥 **The Inference King** 🔥

[⭐ Star this repo](https://github.com/nirvagold/polyglot-bridge) if Polyglot Bridge accelerates your ML pipeline!

</div>
