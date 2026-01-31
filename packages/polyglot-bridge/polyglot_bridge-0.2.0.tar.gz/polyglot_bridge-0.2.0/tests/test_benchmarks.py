"""
Benchmark comparison tests
Property 6: Algorithmic Equivalence
Validates: Requirements 5.1
"""

import pytest
from hypothesis import given, strategies as st, settings
import polyglot_bridge
import sys
sys.path.insert(0, 'python')
from benchmarks import python_sum_of_squares, python_matrix_multiply, python_transform


class TestAlgorithmicEquivalence:
    """
    Property 6: Algorithmic Equivalence
    Validates: Requirements 5.1
    """
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                               min_value=-1e10, max_value=1e10),
                    min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_sum_of_squares_equivalence(self, numbers):
        """Rust and Python implementations produce equivalent results"""
        python_result = python_sum_of_squares(numbers)
        rust_result = polyglot_bridge.sum_of_squares(numbers)
        
        # Allow small floating-point differences
        if python_result != 0:
            relative_error = abs(python_result - rust_result) / abs(python_result)
            assert relative_error < 1e-10, f"Results differ: Python={python_result}, Rust={rust_result}"
        else:
            assert abs(python_result - rust_result) < 1e-10
    
    @given(
        st.integers(min_value=1, max_value=20),  # rows_a
        st.integers(min_value=1, max_value=20),  # cols_a / rows_b
        st.integers(min_value=1, max_value=20),  # cols_b
    )
    @settings(max_examples=30)
    def test_matrix_multiply_equivalence(self, rows_a, cols_a, cols_b):
        """Rust and Python matrix multiplication produce equivalent results"""
        # Generate matrices
        a = [[float(i * cols_a + j) for j in range(cols_a)] for i in range(rows_a)]
        b = [[float(i * cols_b + j) for j in range(cols_b)] for i in range(cols_a)]
        
        python_result = python_matrix_multiply(a, b)
        rust_result = polyglot_bridge.matrix_multiply(a, b)
        
        # Check dimensions
        assert len(python_result) == len(rust_result)
        assert len(python_result[0]) == len(rust_result[0])
        
        # Check values with tolerance
        for i in range(len(python_result)):
            for j in range(len(python_result[0])):
                py_val = python_result[i][j]
                rust_val = rust_result[i][j]
                
                if py_val != 0:
                    relative_error = abs(py_val - rust_val) / abs(py_val)
                    assert relative_error < 1e-10, f"Results differ at [{i}][{j}]: Python={py_val}, Rust={rust_val}"
                else:
                    assert abs(py_val - rust_val) < 1e-10
    
    @given(
        st.lists(st.floats(allow_nan=False, allow_infinity=False,
                          min_value=-1e10, max_value=1e10),
                min_size=1, max_size=1000),
        st.floats(allow_nan=False, allow_infinity=False,
                 min_value=-1e10, max_value=1e10)
    )
    @settings(max_examples=50)
    def test_parallel_transform_equivalence(self, data, factor):
        """Rust parallel and Python sequential produce equivalent results"""
        python_result = python_transform(data, factor)
        rust_result = polyglot_bridge.parallel_transform(data, factor)
        
        assert len(python_result) == len(rust_result)
        
        for i in range(len(python_result)):
            py_val = python_result[i]
            rust_val = rust_result[i]
            
            if py_val != 0:
                relative_error = abs(py_val - rust_val) / abs(py_val)
                assert relative_error < 1e-10, f"Results differ at [{i}]: Python={py_val}, Rust={rust_val}"
            else:
                assert abs(py_val - rust_val) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
