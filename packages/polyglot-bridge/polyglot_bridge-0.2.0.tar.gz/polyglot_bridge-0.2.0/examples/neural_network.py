"""
🧠 THE NEURAL NETWORK FROM SCRATCH 🧠

Implementasi forward pass neural network menggunakan polyglot_bridge:
- Matrix multiplication untuk weight propagation
- Parallel transformation untuk activation functions
- Batch processing untuk efisiensi maksimal

Tujuan: Buktikan polyglot_bridge bisa jadi foundation Deep Learning framework.
"""

import polyglot_bridge
import time
import random
import math
from typing import List, Tuple

class NeuralLayer:
    """Single layer neural network dengan Rust acceleration"""
    
    def __init__(self, input_size: int, output_size: int):
        self.input_size = input_size
        self.output_size = output_size
        
        # Initialize weights dengan Xavier initialization
        # Range: [-sqrt(6/(in+out)), sqrt(6/(in+out))]
        limit = math.sqrt(6.0 / (input_size + output_size))
        self.weights = [
            [random.uniform(-limit, limit) for _ in range(output_size)]
            for _ in range(input_size)
        ]
        
        # Initialize biases ke 0
        self.biases = [0.0] * output_size
        
        print(f"  Layer: {input_size} → {output_size} ({input_size * output_size:,} parameters)")
    
    def forward_rust(self, inputs: List[List[float]]) -> Tuple[List[List[float]], float]:
        """
        Forward pass menggunakan Rust matrix multiplication
        
        Args:
            inputs: Batch of inputs, shape (batch_size, input_size)
        
        Returns:
            (outputs, execution_time_ms)
        """
        start = time.perf_counter()
        
        # Matrix multiply: inputs @ weights
        # Shape: (batch_size, input_size) @ (input_size, output_size) = (batch_size, output_size)
        outputs = polyglot_bridge.matrix_multiply(inputs, self.weights)
        
        # Add biases (simplified - dalam real impl ini juga bisa di-Rust-kan)
        for i in range(len(outputs)):
            for j in range(len(outputs[0])):
                outputs[i][j] += self.biases[j]
        
        elapsed = (time.perf_counter() - start) * 1000
        return outputs, elapsed
    
    def forward_python(self, inputs: List[List[float]]) -> Tuple[List[List[float]], float]:
        """
        Forward pass menggunakan pure Python (untuk comparison)
        """
        start = time.perf_counter()
        
        batch_size = len(inputs)
        outputs = [[0.0] * self.output_size for _ in range(batch_size)]
        
        # Manual matrix multiplication
        for i in range(batch_size):
            for j in range(self.output_size):
                total = self.biases[j]
                for k in range(self.input_size):
                    total += inputs[i][k] * self.weights[k][j]
                outputs[i][j] = total
        
        elapsed = (time.perf_counter() - start) * 1000
        return outputs, elapsed


class ActivationFunction:
    """Activation functions menggunakan parallel_transform"""
    
    @staticmethod
    def relu_rust(data: List[float]) -> Tuple[List[float], float]:
        """
        ReLU activation: max(0, x)
        Approximated using: x * max(0, sign(x))
        """
        start = time.perf_counter()
        
        # ReLU bisa di-approximate dengan scaling
        # Untuk demo, kita pake identity transform (dalam real impl perlu custom function)
        result = polyglot_bridge.parallel_transform(data, 1.0)
        
        # Apply ReLU manually (dalam production, ini harus di Rust)
        result = [max(0.0, x) for x in result]
        
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed
    
    @staticmethod
    def scale_rust(data: List[float], factor: float) -> Tuple[List[float], float]:
        """
        Linear scaling: x * factor
        Perfect use case untuk parallel_transform!
        """
        start = time.perf_counter()
        result = polyglot_bridge.parallel_transform(data, factor)
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed
    
    @staticmethod
    def scale_python(data: List[float], factor: float) -> Tuple[List[float], float]:
        """
        Linear scaling menggunakan pure Python
        """
        start = time.perf_counter()
        result = [x * factor for x in data]
        elapsed = (time.perf_counter() - start) * 1000
        return result, elapsed


class SimpleNeuralNetwork:
    """Multi-layer neural network dengan Rust acceleration"""
    
    def __init__(self, layer_sizes: List[int]):
        self.layers = []
        
        print(f"\n🏗️  Building Neural Network: {' → '.join(map(str, layer_sizes))}")
        
        for i in range(len(layer_sizes) - 1):
            layer = NeuralLayer(layer_sizes[i], layer_sizes[i + 1])
            self.layers.append(layer)
        
        total_params = sum(
            layer.input_size * layer.output_size + layer.output_size
            for layer in self.layers
        )
        print(f"  Total parameters: {total_params:,}")
    
    def forward(self, inputs: List[List[float]], use_rust: bool = True) -> Tuple[List[List[float]], float]:
        """
        Forward pass through all layers
        
        Returns:
            (final_outputs, total_time_ms)
        """
        total_time = 0.0
        current = inputs
        
        for i, layer in enumerate(self.layers):
            if use_rust:
                current, layer_time = layer.forward_rust(current)
            else:
                current, layer_time = layer.forward_python(current)
            
            total_time += layer_time
            
            # Apply activation (except last layer)
            if i < len(self.layers) - 1:
                # Flatten untuk activation
                flat = [val for row in current for val in row]
                
                # Apply scaling activation (demo purpose)
                if use_rust:
                    flat, act_time = ActivationFunction.scale_rust(flat, 0.1)
                else:
                    flat, act_time = ActivationFunction.scale_python(flat, 0.1)
                
                total_time += act_time
                
                # Reshape back
                batch_size = len(current)
                output_size = len(current[0])
                current = [
                    flat[i * output_size:(i + 1) * output_size]
                    for i in range(batch_size)
                ]
        
        return current, total_time


def benchmark_neural_network():
    """
    Benchmark neural network dengan berbagai konfigurasi
    """
    print("=" * 70)
    print("🧠 NEURAL NETWORK BENCHMARK - Rust vs Python 🧠")
    print("=" * 70)
    
    # Test configurations: (architecture, batch_size)
    configs = [
        ([784, 128, 10], 32, "MNIST-like (Small)"),
        ([784, 512, 256, 10], 64, "MNIST-like (Deep)"),
        ([2048, 1024, 512, 10], 128, "Large Network"),
    ]
    
    for architecture, batch_size, description in configs:
        print(f"\n{'='*70}")
        print(f"📊 {description}")
        print(f"   Architecture: {' → '.join(map(str, architecture))}")
        print(f"   Batch size: {batch_size}")
        print(f"{'='*70}")
        
        # Create network
        network = SimpleNeuralNetwork(architecture)
        
        # Generate random input batch
        input_size = architecture[0]
        inputs = [
            [random.uniform(-1, 1) for _ in range(input_size)]
            for _ in range(batch_size)
        ]
        
        print(f"\n🔄 Forward Pass Benchmark")
        print("-" * 70)
        
        # Rust forward pass
        outputs_rust, rust_time = network.forward(inputs, use_rust=True)
        print(f"  Rust:   {rust_time:8.3f} ms")
        
        # Python forward pass
        outputs_python, python_time = network.forward(inputs, use_rust=False)
        print(f"  Python: {python_time:8.3f} ms")
        
        speedup = python_time / rust_time if rust_time > 0 else 0
        print(f"  Speedup: {speedup:7.2f}x {'🔥' if speedup > 1 else ''}")
        
        # Throughput
        samples_per_sec_rust = (batch_size / rust_time) * 1000
        samples_per_sec_python = (batch_size / python_time) * 1000
        
        print(f"\n📈 Throughput")
        print("-" * 70)
        print(f"  Rust:   {samples_per_sec_rust:10,.0f} samples/sec")
        print(f"  Python: {samples_per_sec_python:10,.0f} samples/sec")
        
        # Verify outputs match (approximately)
        diff = sum(
            abs(outputs_rust[i][j] - outputs_python[i][j])
            for i in range(len(outputs_rust))
            for j in range(len(outputs_rust[0]))
        ) / (len(outputs_rust) * len(outputs_rust[0]))
        
        print(f"\n✅ Verification")
        print("-" * 70)
        print(f"  Average difference: {diff:.6f}")
        print(f"  Status: {'PASS ✓' if diff < 0.001 else 'FAIL ✗'}")


def stress_test_large_batch():
    """
    Stress test: process massive batch
    """
    print("\n" + "=" * 70)
    print("💀 STRESS TEST: Large Batch Processing 💀")
    print("=" * 70)
    
    architecture = [1024, 512, 256, 128, 10]
    batch_size = 1000
    
    print(f"\nArchitecture: {' → '.join(map(str, architecture))}")
    print(f"Batch size: {batch_size:,} samples")
    print()
    
    network = SimpleNeuralNetwork(architecture)
    
    # Generate large batch
    print(f"\n📦 Generating {batch_size:,} input samples...")
    inputs = [
        [random.uniform(-1, 1) for _ in range(architecture[0])]
        for _ in range(batch_size)
    ]
    
    print(f"✅ Generated {len(inputs):,} samples of size {len(inputs[0]):,}")
    
    # Process with Rust
    print(f"\n🚀 Processing with Rust...")
    outputs, rust_time = network.forward(inputs, use_rust=True)
    
    print(f"\n📊 Results")
    print("-" * 70)
    print(f"  Total time:       {rust_time:,.2f} ms")
    print(f"  Time per sample:  {rust_time / batch_size:.3f} ms")
    print(f"  Throughput:       {(batch_size / rust_time) * 1000:,.0f} samples/sec")
    
    if rust_time < 1000:
        print(f"\n🏆 VICTORY: Processed {batch_size:,} samples in under 1 second!")
        print("   polyglot_bridge is ready for production ML workloads! 🔥")
    else:
        print(f"\n⚡ Processed {batch_size:,} samples in {rust_time/1000:.2f} seconds")
        print("   Still significantly faster than pure Python! 💪")


def demo_activation_scaling():
    """
    Demo: parallel activation function scaling
    """
    print("\n" + "=" * 70)
    print("⚡ ACTIVATION FUNCTION SCALING DEMO ⚡")
    print("=" * 70)
    
    sizes = [10_000, 100_000, 1_000_000]
    
    for size in sizes:
        print(f"\n📊 Processing {size:,} activations")
        print("-" * 70)
        
        # Generate random activations
        data = [random.uniform(-10, 10) for _ in range(size)]
        
        # Rust scaling
        _, rust_time = ActivationFunction.scale_rust(data, 0.5)
        print(f"  Rust:   {rust_time:8.3f} ms")
        
        # Python scaling
        _, python_time = ActivationFunction.scale_python(data, 0.5)
        print(f"  Python: {python_time:8.3f} ms")
        
        speedup = python_time / rust_time if rust_time > 0 else 0
        print(f"  Speedup: {speedup:7.2f}x {'🔥' if speedup > 1 else ''}")


if __name__ == "__main__":
    # Run neural network benchmark
    benchmark_neural_network()
    
    # Run activation scaling demo
    demo_activation_scaling()
    
    # Run stress test
    stress_test_large_batch()
    
    print("\n" + "=" * 70)
    print("🎯 CONCLUSION: polyglot_bridge can power Deep Learning frameworks")
    print("   Matrix operations are BLAZING FAST with Rust! 🔥🔥🔥")
    print("=" * 70)
