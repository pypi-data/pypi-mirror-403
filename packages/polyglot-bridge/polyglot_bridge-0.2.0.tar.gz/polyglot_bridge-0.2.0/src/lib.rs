use pyo3::prelude::*;

pub mod error;
pub mod core;

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
    core::math::sum_of_squares(&numbers).map_err(|e| e.into())
}

/// Multiply two matrices.
///
/// Args:
///     a (List[List[float]]): First matrix (m x n)
///     b (List[List[float]]): Second matrix (n x p)
///
/// Returns:
///     List[List[float]]: Result matrix (m x p)
///
/// Raises:
///     ValueError: If matrices are empty or dimensions don't match
///
/// Example:
///     >>> import polyglot_bridge
///     >>> a = [[1.0, 2.0], [3.0, 4.0]]
///     >>> b = [[5.0, 6.0], [7.0, 8.0]]
///     >>> polyglot_bridge.matrix_multiply(a, b)
///     [[19.0, 22.0], [43.0, 50.0]]
#[pyfunction]
fn matrix_multiply(a: Vec<Vec<f64>>, b: Vec<Vec<f64>>) -> PyResult<Vec<Vec<f64>>> {
    core::math::matrix_multiply(&a, &b).map_err(|e| e.into())
}

/// Transform data in parallel by multiplying each element by a factor.
///
/// Args:
///     data (List[float]): Input data to transform
///     factor (float): Multiplication factor
///
/// Returns:
///     List[float]: Transformed data
///
/// Raises:
///     ValueError: If the input list is empty
///
/// Example:
///     >>> import polyglot_bridge
///     >>> polyglot_bridge.parallel_transform([1.0, 2.0, 3.0], 2.0)
///     [2.0, 4.0, 6.0]
#[pyfunction]
fn parallel_transform(data: Vec<f64>, factor: f64) -> PyResult<Vec<f64>> {
    core::parallel::parallel_transform(&data, factor).map_err(|e| e.into())
}

/// Python module definition
#[pymodule]
fn polyglot_bridge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Legacy List-based operations (for backward compatibility)
    m.add_function(wrap_pyfunction!(sum_of_squares, m)?)?;
    m.add_function(wrap_pyfunction!(matrix_multiply, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_transform, m)?)?;
    
    // 🚀 NEXT-GEN: Zero-Copy NumPy Operations (THE GAME CHANGER)
    m.add_function(wrap_pyfunction!(core::numpy_ops::matmul_numpy, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::matmul_numpy_f32, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::parallel_map_numpy, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::parallel_map_numpy_f32, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::sum_of_squares_numpy, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::sum_of_squares_numpy_f32, m)?)?;
    
    // 🔥 FUSED OPERATIONS (THE EFFICIENCY PLAY)
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_linear, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_linear_f32, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_linear_relu, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_linear_relu_f32, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_dropout_add, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_layer_norm, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::fused_softmax, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::relu_numpy, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::relu_numpy_f32, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::sigmoid_numpy, m)?)?;
    m.add_function(wrap_pyfunction!(core::numpy_ops::sigmoid_numpy_f32, m)?)?;
    
    Ok(())
}
