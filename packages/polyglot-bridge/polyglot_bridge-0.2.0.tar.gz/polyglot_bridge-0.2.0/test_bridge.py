#!/usr/bin/env python3
"""Test script to verify The Polyglot Bridge is working"""

import polyglot_bridge

print("🌉 Testing The Polyglot Bridge 🌉\n")

# Test 1: sum_of_squares
print("Test 1: sum_of_squares")
numbers = [1.0, 2.0, 3.0, 4.0]
result = polyglot_bridge.sum_of_squares(numbers)
print(f"  Input: {numbers}")
print(f"  Result: {result}")
print(f"  Expected: 30.0")
print(f"  ✅ PASS" if result == 30.0 else f"  ❌ FAIL")
print()

# Test 2: matrix_multiply
print("Test 2: matrix_multiply")
a = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
b = [[7.0, 8.0], [9.0, 10.0], [11.0, 12.0]]
result = polyglot_bridge.matrix_multiply(a, b)
print(f"  Matrix A (2x3): {a}")
print(f"  Matrix B (3x2): {b}")
print(f"  Result (2x2): {result}")
expected = [[58.0, 64.0], [139.0, 154.0]]
print(f"  Expected: {expected}")
print(f"  ✅ PASS" if result == expected else f"  ❌ FAIL")
print()

# Test 3: parallel_transform
print("Test 3: parallel_transform")
data = [1.0, 2.0, 3.0, 4.0, 5.0]
factor = 3.0
result = polyglot_bridge.parallel_transform(data, factor)
print(f"  Input: {data}")
print(f"  Factor: {factor}")
print(f"  Result: {result}")
expected = [3.0, 6.0, 9.0, 12.0, 15.0]
print(f"  Expected: {expected}")
print(f"  ✅ PASS" if result == expected else f"  ❌ FAIL")
print()

# Test 4: Error handling - dimension mismatch
print("Test 4: Error handling (dimension mismatch)")
try:
    a = [[1.0, 2.0]]
    b = [[3.0], [4.0], [5.0]]
    result = polyglot_bridge.matrix_multiply(a, b)
    print("  ❌ FAIL - Should have raised ValueError")
except ValueError as e:
    print(f"  Caught ValueError: {e}")
    print(f"  ✅ PASS - Correct error type")
print()

# Test 5: Error handling - empty input
print("Test 5: Error handling (empty input)")
try:
    result = polyglot_bridge.sum_of_squares([])
    print("  ❌ FAIL - Should have raised ValueError")
except ValueError as e:
    print(f"  Caught ValueError: {e}")
    print(f"  ✅ PASS - Correct error type")
print()

print("🎉 The Polyglot Bridge is ALIVE! Python ↔ Rust connection established! 🎉")
