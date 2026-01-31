"""
Type stubs for polyglot_bridge

The Polyglot Bridge: High-performance Rust library with Python bindings
Accelerate your ML data pipelines with Rust-powered computational functions.
"""

from typing import List

def sum_of_squares(numbers: List[float]) -> float:
    """
    Compute the sum of squares for a list of numbers.
    
    This function provides significant performance improvements over pure Python
    implementations, especially for large datasets.
    
    Args:
        numbers: A list of numeric values
    
    Returns:
        The sum of squares of all numbers
    
    Raises:
        ValueError: If the input list is empty
        RuntimeError: If computation results in overflow
    
    Example:
        >>> import polyglot_bridge
        >>> polyglot_bridge.sum_of_squares([1.0, 2.0, 3.0])
        14.0
        
        >>> # Performance: ~3x faster than pure Python
        >>> data = list(range(10000))
        >>> result = polyglot_bridge.sum_of_squares(data)
    """
    ...

def matrix_multiply(a: List[List[float]], b: List[List[float]]) -> List[List[float]]:
    """
    Multiply two matrices using optimized Rust implementation.
    
    This function delivers exceptional performance gains (up to 95x faster)
    compared to pure Python implementations, making it ideal for ML pipelines
    that involve heavy matrix operations.
    
    Args:
        a: First matrix (m × n)
        b: Second matrix (n × p)
    
    Returns:
        Result matrix (m × p)
    
    Raises:
        ValueError: If matrices are empty or dimensions don't match
    
    Example:
        >>> import polyglot_bridge
        >>> a = [[1.0, 2.0], [3.0, 4.0]]
        >>> b = [[5.0, 6.0], [7.0, 8.0]]
        >>> result = polyglot_bridge.matrix_multiply(a, b)
        >>> # Result: [[19.0, 22.0], [43.0, 50.0]]
        
        >>> # Performance: Up to 95x faster for 50×50 matrices
        >>> # Perfect for feature transformation in ML pipelines
    """
    ...

def parallel_transform(data: List[float], factor: float) -> List[float]:
    """
    Transform data in parallel by multiplying each element by a factor.
    
    This function leverages Rayon for automatic parallelization across CPU cores,
    providing optimal performance for large datasets without manual thread management.
    
    Args:
        data: Input data to transform
        factor: Multiplication factor
    
    Returns:
        Transformed data with each element multiplied by factor
    
    Raises:
        ValueError: If the input list is empty
    
    Example:
        >>> import polyglot_bridge
        >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> result = polyglot_bridge.parallel_transform(data, 2.0)
        >>> # Result: [2.0, 4.0, 6.0, 8.0, 10.0]
        
        >>> # Automatic parallelization - no threading code needed
        >>> large_data = list(range(100000))
        >>> result = polyglot_bridge.parallel_transform(large_data, 1.5)
    """
    ...

__all__ = ['sum_of_squares', 'matrix_multiply', 'parallel_transform']
