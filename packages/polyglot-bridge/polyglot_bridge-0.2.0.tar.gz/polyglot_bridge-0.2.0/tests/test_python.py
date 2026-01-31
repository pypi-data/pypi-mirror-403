"""
Python integration tests for The Polyglot Bridge
Tests all PyO3 bindings with property-based testing using Hypothesis
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import polyglot_bridge


# Task 6.1: Test module import
class TestModuleImport:
    """Validates: Requirements 1.1"""
    
    def test_module_can_be_imported(self):
        """Test that polyglot_bridge module can be imported"""
        assert polyglot_bridge is not None
    
    def test_all_functions_accessible(self):
        """Verify all expected functions are accessible"""
        assert hasattr(polyglot_bridge, 'sum_of_squares')
        assert hasattr(polyglot_bridge, 'matrix_multiply')
        assert hasattr(polyglot_bridge, 'parallel_transform')
    
    def test_functions_are_callable(self):
        """Verify functions are callable"""
        assert callable(polyglot_bridge.sum_of_squares)
        assert callable(polyglot_bridge.matrix_multiply)
        assert callable(polyglot_bridge.parallel_transform)


# Task 6.2: Property test for type conversion round trip
class TestTypeConversionRoundTrip:
    """
    Property 1: Type Conversion Round Trip
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False, 
                               min_value=-1e100, max_value=1e100), 
                    min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_float_list_roundtrip_sum_of_squares(self, numbers):
        """For any valid list of floats, type conversion should work correctly"""
        result = polyglot_bridge.sum_of_squares(numbers)
        assert isinstance(result, float)
        assert not (result != result)  # Not NaN
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                               min_value=-1e50, max_value=1e50),
                    min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_float_list_roundtrip_parallel_transform(self, data):
        """For any valid list of floats, parallel_transform should preserve types"""
        factor = 2.0
        result = polyglot_bridge.parallel_transform(data, factor)
        assert isinstance(result, list)
        assert len(result) == len(data)
        assert all(isinstance(x, float) for x in result)
    
    @given(
        st.integers(min_value=1, max_value=10),  # rows
        st.integers(min_value=1, max_value=10),  # cols
    )
    @settings(max_examples=50)
    def test_matrix_roundtrip(self, rows, cols):
        """For any valid matrix dimensions, type conversion should work"""
        # Generate properly shaped matrix A
        matrix_a = [[float(i * cols + j) for j in range(cols)] for i in range(rows)]
        
        # Create compatible matrix B (cols x 2)
        matrix_b = [[1.0, 2.0] for _ in range(cols)]
        
        result = polyglot_bridge.matrix_multiply(matrix_a, matrix_b)
        assert isinstance(result, list)
        assert len(result) == rows
        assert all(len(row) == 2 for row in result)
        assert all(isinstance(row, list) for row in result)
        assert all(isinstance(val, float) for row in result for val in row)


# Task 6.3: Property test for function call type safety
class TestFunctionCallTypeSafety:
    """
    Property 2: Function Call Type Safety
    Validates: Requirements 1.2
    """
    
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                               min_value=-1e100, max_value=1e100),
                    min_size=1, max_size=1000))
    @settings(max_examples=100)
    def test_sum_of_squares_returns_float(self, numbers):
        """For any list of valid floats, sum_of_squares returns a float"""
        result = polyglot_bridge.sum_of_squares(numbers)
        assert isinstance(result, float)
    
    @given(
        st.lists(st.floats(allow_nan=False, allow_infinity=False,
                          min_value=-1e50, max_value=1e50),
                min_size=1, max_size=100),
        st.floats(allow_nan=False, allow_infinity=False,
                 min_value=-1e50, max_value=1e50)
    )
    @settings(max_examples=100)
    def test_parallel_transform_returns_list(self, data, factor):
        """For any valid inputs, parallel_transform returns a list"""
        result = polyglot_bridge.parallel_transform(data, factor)
        assert isinstance(result, list)
        assert len(result) == len(data)


# Task 6.4: Property test for error conversion
class TestErrorConversion:
    """
    Property 3: Error Conversion Completeness
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    
    def test_empty_input_raises_value_error_sum_of_squares(self):
        """Empty input should raise ValueError with descriptive message"""
        with pytest.raises(ValueError) as exc_info:
            polyglot_bridge.sum_of_squares([])
        assert "empty" in str(exc_info.value).lower()
    
    def test_empty_input_raises_value_error_parallel_transform(self):
        """Empty input should raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            polyglot_bridge.parallel_transform([], 2.0)
        assert "empty" in str(exc_info.value).lower()
    
    def test_dimension_mismatch_raises_value_error(self):
        """Dimension mismatch should raise ValueError with descriptive message"""
        a = [[1.0, 2.0]]
        b = [[3.0], [4.0], [5.0]]
        with pytest.raises(ValueError) as exc_info:
            polyglot_bridge.matrix_multiply(a, b)
        assert "dimension" in str(exc_info.value).lower()
    
    def test_empty_matrix_raises_value_error(self):
        """Empty matrix should raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            polyglot_bridge.matrix_multiply([], [[1.0]])
        assert "empty" in str(exc_info.value).lower()
    
    def test_overflow_raises_runtime_error(self):
        """Overflow should raise RuntimeError"""
        huge_numbers = [1e200, 1e200]
        with pytest.raises(RuntimeError) as exc_info:
            polyglot_bridge.sum_of_squares(huge_numbers)
        assert "overflow" in str(exc_info.value).lower()


# Task 6.5: Property test for invalid type rejection
class TestInvalidTypeRejection:
    """
    Property 4: Invalid Type Rejection
    Validates: Requirements 3.3, 4.6
    """
    
    def test_sum_of_squares_rejects_strings(self):
        """Passing strings should raise TypeError"""
        with pytest.raises(TypeError):
            polyglot_bridge.sum_of_squares(["not", "numbers"])
    
    def test_sum_of_squares_rejects_none(self):
        """Passing None should raise TypeError"""
        with pytest.raises(TypeError):
            polyglot_bridge.sum_of_squares(None)
    
    def test_matrix_multiply_rejects_invalid_types(self):
        """Passing invalid types should raise TypeError"""
        with pytest.raises(TypeError):
            polyglot_bridge.matrix_multiply("not a matrix", [[1.0]])
    
    def test_parallel_transform_rejects_invalid_factor(self):
        """Passing invalid factor type should raise TypeError"""
        with pytest.raises(TypeError):
            polyglot_bridge.parallel_transform([1.0, 2.0], "not a number")


# Task 6.6: Test for panic safety
class TestPanicSafety:
    """
    Property 5: Panic Safety
    Validates: Requirements 3.5
    """
    
    @given(st.lists(st.floats(), min_size=0, max_size=1000))
    @settings(max_examples=100, deadline=None)
    def test_sum_of_squares_never_crashes(self, numbers):
        """Any input should either succeed or raise Python exception, never crash"""
        try:
            result = polyglot_bridge.sum_of_squares(numbers)
            # If it succeeds, result should be valid
            assert isinstance(result, float) or result is None
        except (ValueError, RuntimeError, TypeError):
            # Expected exceptions are fine
            pass
        # If we get here, Python interpreter didn't crash
    
    @given(
        st.lists(st.lists(st.floats(), min_size=0, max_size=10), 
                min_size=0, max_size=10),
        st.lists(st.lists(st.floats(), min_size=0, max_size=10),
                min_size=0, max_size=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_matrix_multiply_never_crashes(self, a, b):
        """Any matrix input should either succeed or raise Python exception"""
        try:
            result = polyglot_bridge.matrix_multiply(a, b)
            assert isinstance(result, list) or result is None
        except (ValueError, RuntimeError, TypeError):
            pass
        # Python interpreter still alive


# Task 6.7: Unit tests for Python API ergonomics
class TestPythonAPIErgonomics:
    """Validates: Requirements 1.3, 7.2"""
    
    def test_sum_of_squares_has_docstring(self):
        """Verify sum_of_squares has docstring"""
        assert polyglot_bridge.sum_of_squares.__doc__ is not None
        assert len(polyglot_bridge.sum_of_squares.__doc__) > 0
    
    def test_matrix_multiply_has_docstring(self):
        """Verify matrix_multiply has docstring"""
        assert polyglot_bridge.matrix_multiply.__doc__ is not None
        assert len(polyglot_bridge.matrix_multiply.__doc__) > 0
    
    def test_parallel_transform_has_docstring(self):
        """Verify parallel_transform has docstring"""
        assert polyglot_bridge.parallel_transform.__doc__ is not None
        assert len(polyglot_bridge.parallel_transform.__doc__) > 0
    
    def test_docstrings_contain_args_section(self):
        """Docstrings should document arguments"""
        doc = polyglot_bridge.sum_of_squares.__doc__
        assert "Args:" in doc or "args:" in doc.lower()
    
    def test_docstrings_contain_returns_section(self):
        """Docstrings should document return values"""
        doc = polyglot_bridge.sum_of_squares.__doc__
        assert "Returns:" in doc or "returns:" in doc.lower()
    
    def test_docstrings_contain_raises_section(self):
        """Docstrings should document exceptions"""
        doc = polyglot_bridge.sum_of_squares.__doc__
        assert "Raises:" in doc or "raises:" in doc.lower()
    
    def test_help_displays_documentation(self, capsys):
        """Test that help() displays proper documentation"""
        help(polyglot_bridge.sum_of_squares)
        captured = capsys.readouterr()
        assert "sum_of_squares" in captured.out


# Stress tests
class TestStressTests:
    """Stress tests to find edge cases and performance issues"""
    
    def test_large_array_sum_of_squares(self):
        """Test with large array (10k elements)"""
        data = list(range(10000))
        result = polyglot_bridge.sum_of_squares(data)
        assert isinstance(result, float)
        assert result > 0
    
    def test_large_matrix_multiply(self):
        """Test with larger matrices"""
        a = [[float(i + j) for j in range(50)] for i in range(50)]
        b = [[float(i + j) for j in range(50)] for i in range(50)]
        result = polyglot_bridge.matrix_multiply(a, b)
        assert len(result) == 50
        assert len(result[0]) == 50
    
    def test_parallel_transform_large_dataset(self):
        """Test parallel processing with 100k elements"""
        data = list(range(100000))
        result = polyglot_bridge.parallel_transform(data, 2.0)
        assert len(result) == 100000
        assert result[0] == 0.0
        assert result[99999] == 199998.0
    
    def test_stress_parallel_transform_hypothesis(self):
        """Stress test parallel_transform with large dataset"""
        # Simple deterministic stress test instead of property-based
        data = [float(i) for i in range(50000)]
        result = polyglot_bridge.parallel_transform(data, 1.5)
        assert len(result) == 50000
        # Verify correctness on samples
        assert result[0] == 0.0
        assert result[1000] == 1500.0
        assert result[49999] == 74998.5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
