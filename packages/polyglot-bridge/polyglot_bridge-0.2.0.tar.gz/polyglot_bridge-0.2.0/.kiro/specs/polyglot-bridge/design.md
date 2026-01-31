# Design Document: The Polyglot Bridge

## Overview

The Polyglot Bridge is a high-performance Rust library that exposes computational functions to Python through PyO3 bindings. The architecture prioritizes zero-cost abstractions, efficient memory management, and seamless cross-language interoperability while maintaining type safety and proper error handling.

The library implements performance-critical operations (mathematical computations, data processing) in Rust and exposes them through a clean Python API. The design leverages Rust's ownership system for memory safety, PyO3's automatic type conversion for ergonomic Python integration, and Rayon for parallel processing where beneficial.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Python Application                    │
└─────────────────────┬───────────────────────────────────┘
                      │ Python API calls
                      ▼
┌─────────────────────────────────────────────────────────┐
│              PyO3 Bindings Layer (lib.rs)               │
│  - Function exports with #[pyfunction]                  │
│  - Type conversion (Python ↔ Rust)                      │
│  - Error translation (Result → PyErr)                   │
└─────────────────────┬───────────────────────────────────┘
                      │ Rust function calls
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Core Rust Library (core/)                  │
│  - Mathematical operations (math.rs)                    │
│  - Data processing (data.rs)                            │
│  - Parallel algorithms (parallel.rs)                    │
└─────────────────────────────────────────────────────────┘
```

### Module Structure

```
polyglot-bridge/
├── src/
│   ├── lib.rs           # PyO3 bindings and Python module definition
│   ├── core/
│   │   ├── mod.rs       # Core module exports
│   │   ├── math.rs      # Mathematical operations
│   │   ├── data.rs      # Data processing functions
│   │   └── parallel.rs  # Parallel computation utilities
│   ├── error.rs         # Error types and conversions
│   └── types.rs         # Shared type definitions
├── python/
│   ├── __init__.py      # Python package initialization
│   └── benchmarks.py    # Performance benchmarks
├── tests/
│   ├── test_math.rs     # Rust unit tests
│   └── test_python.py   # Python integration tests
├── benches/
│   └── criterion.rs     # Rust benchmarks using Criterion
├── Cargo.toml
└── pyproject.toml       # Python package configuration
```

## Components and Interfaces

### 1. PyO3 Bindings Layer (`lib.rs`)

**Responsibility:** Expose Rust functions to Python with automatic type conversion and error handling.

**Key Functions:**

```rust
use pyo3::prelude::*;
use pyo3::exceptions::PyRuntimeError;

/// Compute the sum of squares for a list of numbers
#[pyfunction]
fn sum_of_squares(numbers: Vec<f64>) -> PyResult<f64> {
    core::math::sum_of_squares(&numbers)
        .map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

/// Process a large dataset in parallel
#[pyfunction]
fn parallel_transform(data: Vec<f64>, factor: f64) -> PyResult<Vec<f64>> {
    core::parallel::transform(&data, factor)
        .map_err(|e| PyRuntimeError::new_err(e.to_string()))
}

/// Python module definition
#[pymodule]
fn polyglot_bridge(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_of_squares, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_transform, m)?)?;
    Ok(())
}
```

**Type Conversions:**
- `Vec<f64>` ↔ Python `list[float]`
- `String` ↔ Python `str`
- `Result<T, E>` → Python exceptions
- Numeric types: `i64`, `f64` ↔ Python `int`, `float`

### 2. Core Mathematical Operations (`core/math.rs`)

**Responsibility:** Implement CPU-intensive mathematical computations with optimal performance.

**Key Functions:**

```rust
use crate::error::BridgeError;

/// Compute sum of squares with overflow checking
pub fn sum_of_squares(numbers: &[f64]) -> Result<f64, BridgeError> {
    if numbers.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    let result = numbers.iter()
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
    
    let cols_a = a[0].len();
    let rows_b = b.len();
    let cols_b = b[0].len();
    
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
```

### 3. Parallel Data Processing (`core/parallel.rs`)

**Responsibility:** Leverage Rayon for parallel processing of large datasets.

**Key Functions:**

```rust
use rayon::prelude::*;
use crate::error::BridgeError;

/// Transform data in parallel
pub fn transform(data: &[f64], factor: f64) -> Result<Vec<f64>, BridgeError> {
    if data.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    let result: Vec<f64> = data.par_iter()
        .map(|&x| x * factor)
        .collect();
    
    Ok(result)
}

/// Parallel filter and map operation
pub fn filter_map_parallel<F>(data: &[f64], predicate: F) -> Result<Vec<f64>, BridgeError>
where
    F: Fn(f64) -> bool + Sync + Send,
{
    if data.is_empty() {
        return Err(BridgeError::EmptyInput);
    }
    
    let result: Vec<f64> = data.par_iter()
        .filter(|&&x| predicate(x))
        .copied()
        .collect();
    
    Ok(result)
}
```

### 4. Error Handling (`error.rs`)

**Responsibility:** Define error types and provide conversions to Python exceptions.

Using `thiserror` for ergonomic error definitions (Rust best practice):

```rust
use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::PyErr;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BridgeError {
    #[error("Input cannot be empty")]
    EmptyInput,
    
    #[error("Computation resulted in overflow")]
    Overflow,
    
    #[error("Matrix dimensions do not match")]
    DimensionMismatch,
    
    #[error("Invalid type: {0}")]
    InvalidType(String),
    
    #[error("Computation error: {0}")]
    ComputationError(String),
}

impl From<BridgeError> for PyErr {
    fn from(err: BridgeError) -> PyErr {
        match err {
            BridgeError::InvalidType(_) => PyTypeError::new_err(err.to_string()),
            BridgeError::EmptyInput | BridgeError::DimensionMismatch => {
                PyValueError::new_err(err.to_string())
            }
            _ => PyRuntimeError::new_err(err.to_string()),
        }
    }
}
```

## Data Models

### Input/Output Types

**Numeric Arrays:**
```rust
// Rust side
pub type NumericArray = Vec<f64>;
pub type Matrix = Vec<Vec<f64>>;

// Python side (type hints)
from typing import List
NumericArray = List[float]
Matrix = List[List[float]]
```

**Configuration Types:**
```rust
#[derive(Debug, Clone)]
pub struct ComputeConfig {
    pub parallel: bool,
    pub chunk_size: usize,
}

impl Default for ComputeConfig {
    fn default() -> Self {
        Self {
            parallel: true,
            chunk_size: 1000,
        }
    }
}
```

### Memory Management

**Ownership Rules:**
- PyO3 handles memory management across the FFI boundary
- Rust functions accept borrowed slices (`&[T]`) to avoid unnecessary copies
- Return values are moved to Python, transferring ownership
- Large datasets use `Vec` for efficient heap allocation

**Zero-Copy Optimization:**
- Use `&[T]` parameters to avoid copying input data
- PyO3's `FromPyObject` trait handles conversion efficiently
- Return `Vec<T>` directly (moved to Python, no copy)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Type Conversion Round Trip

*For any* valid Python value of supported types (int, float, str, list), converting it to Rust and back to Python should produce an equivalent value.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 2: Function Call Type Safety

*For any* exposed Rust function called with valid Python arguments, the function should execute successfully and return a value of the correct Python type.

**Validates: Requirements 1.2**

### Property 3: Error Conversion Completeness

*For any* Rust error that occurs during computation, the error should be converted to an appropriate Python exception (TypeError, ValueError, or RuntimeError) with a descriptive message.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 4: Invalid Type Rejection

*For any* function call with invalid type arguments, a TypeError should be raised with details about the expected type.

**Validates: Requirements 3.3, 4.6**

### Property 5: Panic Safety

*For any* operation that could cause a Rust panic, the panic should be caught and converted to a Python exception without crashing the Python interpreter.

**Validates: Requirements 3.5**

### Property 6: Algorithmic Equivalence

*For any* computation implemented in both Rust and Python, given the same inputs, both implementations should produce equivalent results (within floating-point tolerance).

**Validates: Requirements 5.1**

## Error Handling

### Error Categories

**1. Input Validation Errors:**
- Empty input arrays → `BridgeError::EmptyInput` → Python `ValueError`
- Dimension mismatches → `BridgeError::DimensionMismatch` → Python `ValueError`
- Invalid types → `BridgeError::InvalidType` → Python `TypeError`

**2. Computation Errors:**
- Numeric overflow → `BridgeError::Overflow` → Python `RuntimeError`
- General computation failures → `BridgeError::ComputationError` → Python `RuntimeError`

**3. Panic Handling:**
- Use `std::panic::catch_unwind` in critical sections
- Convert panics to `PyRuntimeError` with descriptive messages
- Never allow panics to cross FFI boundary

### Error Propagation Pattern

```rust
#[pyfunction]
fn rust_function(data: Vec<f64>) -> PyResult<f64> {
    // Rust Result is automatically converted to PyResult
    core::math::compute(&data)
        .map_err(|e| PyRuntimeError::new_err(e.to_string()))
}
```

### Panic Safety Pattern

```rust
use std::panic::catch_unwind;

#[pyfunction]
fn potentially_panicking_function(data: Vec<f64>) -> PyResult<f64> {
    catch_unwind(|| {
        // Potentially panicking code
        core::math::risky_compute(&data)
    })
    .map_err(|_| PyRuntimeError::new_err("Internal computation error"))
    .and_then(|result| result.map_err(|e| PyRuntimeError::new_err(e.to_string())))
}
```

## Testing Strategy

### Dual Testing Approach

The library requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests:**
- Specific examples demonstrating correct behavior
- Edge cases (empty inputs, boundary values, special numeric values)
- Error conditions (invalid inputs, overflow scenarios)
- Integration between Rust and Python layers

**Property-Based Tests:**
- Universal properties that hold for all inputs
- Type conversion correctness across random inputs
- Error handling consistency
- Algorithmic equivalence between Rust and Python implementations

### Property-Based Testing Configuration

**Library Selection:**
- **Rust:** Use `proptest` crate for property-based testing in Rust
- **Python:** Use `hypothesis` library for property-based testing in Python

**Test Configuration:**
- Minimum 100 iterations per property test
- Each property test must reference its design document property
- Tag format: `// Feature: polyglot-bridge, Property N: [property text]`

**Example Property Test (Rust):**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    // Feature: polyglot-bridge, Property 1: Type Conversion Round Trip
    proptest! {
        #[test]
        fn test_float_vec_roundtrip(data in prop::collection::vec(any::<f64>(), 0..1000)) {
            // This would test the conversion logic
            // In practice, this tests the core Rust functions
            let result = sum_of_squares(&data);
            assert!(result.is_ok() || data.is_empty());
        }
    }
}
```

**Example Property Test (Python):**

```python
from hypothesis import given, strategies as st
import polyglot_bridge

# Feature: polyglot-bridge, Property 2: Function Call Type Safety
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False)))
def test_sum_of_squares_type_safety(numbers):
    """For any list of valid floats, sum_of_squares returns a float."""
    if len(numbers) > 0:
        result = polyglot_bridge.sum_of_squares(numbers)
        assert isinstance(result, float)
```

### Unit Test Coverage

**Rust Unit Tests (`tests/test_math.rs`):**
- Test mathematical correctness with known inputs/outputs
- Test edge cases: empty arrays, single elements, large arrays
- Test error conditions: overflow, invalid dimensions
- Test parallel vs sequential equivalence

**Python Integration Tests (`tests/test_python.py`):**
- Test Python API ergonomics (keyword args, defaults)
- Test type hint availability
- Test docstring presence
- Test error messages are descriptive
- Test cross-platform compatibility

### Performance Benchmarking

**Rust Benchmarks (using Criterion):**
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_sum_of_squares(c: &mut Criterion) {
    let data: Vec<f64> = (0..10000).map(|x| x as f64).collect();
    
    c.bench_function("sum_of_squares_10k", |b| {
        b.iter(|| sum_of_squares(black_box(&data)))
    });
}

criterion_group!(benches, benchmark_sum_of_squares);
criterion_main!(benches);
```

**Python Benchmarks:**
```python
import time
import polyglot_bridge

def benchmark_comparison():
    data = list(range(10000))
    
    # Python implementation
    start = time.perf_counter()
    python_result = sum(x * x for x in data)
    python_time = time.perf_counter() - start
    
    # Rust implementation
    start = time.perf_counter()
    rust_result = polyglot_bridge.sum_of_squares(data)
    rust_time = time.perf_counter() - start
    
    speedup = python_time / rust_time
    print(f"Speedup: {speedup:.2f}x")
```

## Build and Distribution

### Build Configuration

**Cargo.toml:**
```toml
[package]
name = "polyglot-bridge"
version = "0.1.0"
edition = "2024"
rust-version = "1.93"

[lib]
name = "polyglot_bridge"
crate-type = ["cdylib"]

[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
rayon = "1.10"
thiserror = "2.0"

[dev-dependencies]
proptest = "1.5"
criterion = "0.5"

[[bench]]
name = "criterion"
harness = false
```

**pyproject.toml:**
```toml
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "polyglot-bridge"
version = "0.1.0"
description = "High-performance Rust library with Python bindings"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[tool.maturin]
features = ["pyo3/extension-module"]
```

### Build Commands

```bash
# Development build
maturin develop

# Release build
maturin build --release

# Build wheel for distribution
maturin build --release --out dist/

# Install locally
pip install .
```

### Platform Support

- **Linux:** x86_64, aarch64
- **macOS:** x86_64, aarch64 (Apple Silicon)
- **Windows:** x86_64

Maturin handles platform-specific compilation and wheel generation automatically.

## Documentation

### Python API Documentation

Each exposed function includes comprehensive docstrings:

```rust
/// Compute the sum of squares for a list of numbers.
///
/// Args:
///     numbers (List[float]): A list of numeric values
///
/// Returns:
///     float: The sum of squares of all numbers
///
/// Raises:
///     ValueError: If the input list is empty
///     RuntimeError: If computation results in overflow
///
/// Example:
///     >>> import polyglot_bridge
///     >>> polyglot_bridge.sum_of_squares([1.0, 2.0, 3.0])
///     14.0
#[pyfunction]
fn sum_of_squares(numbers: Vec<f64>) -> PyResult<f64> {
    // Implementation
}
```

### Type Stubs

Generate `.pyi` stub files for IDE support:

```python
# polyglot_bridge.pyi
from typing import List

def sum_of_squares(numbers: List[float]) -> float:
    """Compute the sum of squares for a list of numbers."""
    ...

def parallel_transform(data: List[float], factor: float) -> List[float]:
    """Transform data in parallel."""
    ...
```

## Performance Considerations

### Optimization Strategies

1. **Zero-Copy Operations:** Use borrowed slices (`&[T]`) for input parameters
2. **Parallel Processing:** Use Rayon for data-parallel operations on large datasets
3. **Memory Pre-allocation:** Use `Vec::with_capacity()` when output size is known
4. **Iterator Chains:** Leverage Rust's iterator optimizations for transformations
5. **Inline Hints:** Use `#[inline]` for small, frequently-called functions

### Expected Performance Gains

Based on typical Rust vs Python performance characteristics:

- **Mathematical computations:** 10-100x speedup
- **Data transformations:** 5-50x speedup (depending on parallelization)
- **Matrix operations:** 20-200x speedup

Actual performance gains depend on:
- Input size (larger inputs benefit more from Rust)
- Operation complexity (CPU-bound operations benefit most)
- Parallelization opportunities (embarrassingly parallel tasks see largest gains)
